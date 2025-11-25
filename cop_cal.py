from CoolProp.CoolProp import AbstractState, QT_INPUTS, PT_INPUTS, PQ_INPUTS
from scipy.optimize import brentq

def calculate_scroll_cop(refrigerant, t_evap_c, t_cond_c, superheat_k=5, subcooling_k=5, is_efficiency=0.80, motor_efficiency=0.93):
    """
    计算涡旋压缩机的极限 COP。
    
    参数:
    refrigerant (str): 制冷剂名称 (例如 "R410A", "R32", "R290")
    t_evap_c (float): 蒸发温度 (摄氏度)
    t_cond_c (float): 冷凝温度 (摄氏度)
    superheat_k (float): 吸气过热度 (Kelvin/摄氏度差值)，默认 5K
    subcooling_k (float): 液体过冷度 (Kelvin/摄氏度差值)，默认 5K
    is_efficiency (float): 压缩机等熵效率 (0.0-1.0)。涡旋机的高限通常在 0.75-0.85 之间。
    motor_efficiency (float): 电机效率 (0.0-1.0)。高效电机通常在 0.90-0.95 之间。
    """
    
    # 1. 单位转换 (摄氏度 -> 开尔文)
    t_evap_k = t_evap_c + 273.15
    t_cond_k = t_cond_c + 273.15

    # 为混合物定义组分和质量分数
    ref_map = {
        "R454B": {"fluids": "R32&R1234yf", "fractions": [0.689, 0.311]}
    }
    
    step = "Initialization"
    try:
        # 使用高级 AbstractState 接口, 并根据是否为混合物进行不同的初始化
        ref_info = ref_map.get(refrigerant)
        if ref_info:
            # 对于预定义的混合物, 先创建对象, 再设置质量分数
            AS = AbstractState("HEOS", ref_info["fluids"])
            AS.set_mass_fractions(ref_info["fractions"])
        else:
            # 对于纯工质, 直接创建对象
            AS = AbstractState("HEOS", refrigerant)

        # -----------------------------
        # A. 计算卡诺 COP (物理极限)
        # -----------------------------
        cop_carnot = t_evap_k / (t_cond_k - t_evap_k)

        # -----------------------------
        # B. 热力学状态点计算 (基于焓值)
        # -----------------------------
        
        # 1. 确定压力 (根据 cop2.py 逻辑: 蒸发和冷凝温度均视为露点温度 Dew Point)
        step = "Pressure Calculation"
        # 蒸发侧 (Dew Point, Q=1)
        AS.update(QT_INPUTS, 1.0, t_evap_k)
        p_evap = AS.p()
        
        # 冷凝侧 (Dew Point, Q=1) - 修正：原代码使用Bubble Point (Q=0), cop2使用Dew Point (Q=1)
        AS.update(QT_INPUTS, 1.0, t_cond_k)
        p_cond = AS.p()
        
        # 状态点 1: 压缩机吸气口 (Suction)
        step = "Point 1 (Suction)"
        t_suction = t_evap_k + superheat_k
        AS.update(PT_INPUTS, p_evap, t_suction)
        h1 = AS.hmass()
        s1 = AS.smass()

        # 状态点 2 (理想): 等熵排气 (Isentropic Discharge)
        step = "Point 2 (Isentropic Discharge)"
        
        # 定义一个误差函数：输入猜测温度 T，返回 (当前熵 - 目标熵)
        def entropy_difference(T_guess):
            AS.update(PT_INPUTS, p_cond, T_guess)
            return AS.smass() - s1
        
        # 预估排气温度范围：
        # 下限：冷凝压力下的饱和气体温度
        AS.update(PQ_INPUTS, p_cond, 1.0)
        t_min = AS.T() + 0.1 # 稍微加一点避开两相区
        t_max = t_min + 150.0 # 足够宽的范围
        
        # 使用 brentq 算法快速找到让 entropy_difference 为 0 的温度
        try:
            t2_ideal = brentq(entropy_difference, t_min, t_max)
        except ValueError as e:
             raise Exception(f"Isentropic discharge calculation failed (brentq): {e}")

        # 找到 T2 后，直接用 P, T 计算 h2
        AS.update(PT_INPUTS, p_cond, t2_ideal)
        h2_ideal = AS.hmass()
        
        # 状态点 3: 冷凝器出口/膨胀阀前 (Liquid Line)
        step = "Point 3 (Liquid)"
        
        # 先找泡点温度 (Bubble Point)
        AS.update(PQ_INPUTS, p_cond, 0.0)
        t_bubble = AS.T()
        
        # 过冷度是相对于泡点定义的
        t_liquid = t_bubble - subcooling_k
        
        AS.update(PT_INPUTS, p_cond, t_liquid)
        h3 = AS.hmass()
        
        h4 = h3 # 节流过程视为等焓过程

        # -----------------------------
        # C. 能量与功计算
        # -----------------------------
        
        q_cooling = h1 - h4
        w_ideal = h2_ideal - h1
        
        if w_ideal <= 0:
             return {"error": "Ideal work is zero or negative, cannot calculate COP."}

        cop_ideal_cycle = q_cooling / w_ideal
        
        # -----------------------------
        # D. 实际涡旋机极限计算
        # -----------------------------
        
        w_actual = w_ideal / (is_efficiency * motor_efficiency)
        
        if w_actual <= 0:
            return {"error": "Actual work is zero or negative, cannot calculate COP."}

        cop_scroll_limit = q_cooling / w_actual

        return {
            "制冷剂": refrigerant,
            "工况": f"蒸发: {t_evap_c}°C, 冷凝: {t_cond_c}°C",
            "卡诺COP极限 (理论最大值)": round(cop_carnot, 3),
            "理想朗肯循环COP": round(cop_ideal_cycle, 3),
            "涡旋机技术极限COP": round(cop_scroll_limit, 3),
            "详细参数": {
                "等熵效率": is_efficiency,
                "电机效率": motor_efficiency,
                "压缩比": round(p_cond/p_evap, 2),
                "理想排气温度(°C)": round(t2_ideal - 273.15, 2),
                "冷凝出液温度(°C)": round(t_liquid - 273.15, 2)
            }
        }

    except Exception as e:
        return {"error": f"Calculation failed for {refrigerant} at step '{step}': {e}"}

# ==========================================
# 示例运行
# ==========================================
if __name__ == '__main__':
    # 示例包含 R454B 来测试新逻辑的稳健性
    test_cases = [
        ("R410A", 5, 50),
        ("R454B", 5, 50)
    ]

    import json
    
    for r, te, tc in test_cases:
        print(f"Testing {r}...")
        result = calculate_scroll_cop(
            r, 
            te, 
            tc, 
            superheat_k=5, 
            subcooling_k=5, 
            is_efficiency=0.82,
            motor_efficiency=0.96
        )
        print(json.dumps(result, indent=4))
