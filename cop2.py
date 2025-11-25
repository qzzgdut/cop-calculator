import CoolProp as CP
from CoolProp.CoolProp import AbstractState
from scipy.optimize import brentq  # 引入求根函数，非常稳健

def calculate_r454b_cop_robust(t_evap_c, t_cond_c, superheat_k, subcool_k):
    # ============================
    # 1. 初始化制冷剂 R454B
    # ============================
    # 定义混合物 R32/R1234yf
    AS = AbstractState("HEOS", "R32&R1234yf")
    AS.set_mass_fractions([0.689, 0.311])
    
    # 温度单位转换
    T_evap_input = t_evap_c + 273.15
    T_cond_input = t_cond_c + 273.15
    
    print(f"--- 工况: 蒸发 {t_evap_c}°C, 冷凝 {t_cond_c}°C (稳健迭代法) ---")

    # ============================
    # 2. 计算压力 (P-T查询，非常稳定)
    # ============================
    # 蒸发侧 (Dew Point, Q=1)
    AS.update(CP.QT_INPUTS, 1.0, T_evap_input)
    P_evap = AS.p()
    
    # 冷凝侧 (Dew Point, Q=1)
    AS.update(CP.QT_INPUTS, 1.0, T_cond_input)
    P_cond = AS.p()
    
    print(f"蒸发压力 (Dew): {P_evap/1000:.2f} kPa")
    print(f"冷凝压力 (Dew): {P_cond/1000:.2f} kPa")

    # ============================
    # 3. 计算各点状态
    # ============================
    
    # --- 点 1: 吸气口 (蒸发压力, 吸气温度) ---
    T1 = T_evap_input + superheat_k
    AS.update(CP.PT_INPUTS, P_evap, T1) # P-T 查询很稳定
    h1 = AS.hmass()
    s1 = AS.smass() # 目标熵

    # --- 点 2: 排气口 (冷凝压力, s2 = s1) ---
    # 【核心修改】不直接使用 PS_INPUTS，而是自己迭代找温度
    
    # 定义一个误差函数：输入猜测温度 T，返回 (当前熵 - 目标熵)
    def entropy_difference(T_guess):
        AS.update(CP.PT_INPUTS, P_cond, T_guess)
        return AS.smass() - s1
    
    # 预估排气温度范围：
    # 下限：冷凝温度 (气体不可能比冷凝温度低)
    # 上限：冷凝温度 + 100度 (足够宽的范围)
    
    # 获取冷凝温度下的饱和气体温度（作为下限）
    AS.update(CP.PQ_INPUTS, P_cond, 1.0)
    T_min = AS.T() + 0.1 # 稍微加一点避开两相区
    T_max = T_min + 120.0 
    
    # 使用 brentq 算法快速找到让 entropy_difference 为 0 的温度
    try:
        T2 = brentq(entropy_difference, T_min, T_max)
    except ValueError as e:
        print(f"迭代寻找排气温度失败: {e}")
        return

    # 找到 T2 后，直接用 P, T 计算 h2
    AS.update(CP.PT_INPUTS, P_cond, T2)
    h2 = AS.hmass()

    # --- 点 3: 冷凝器出口 (冷凝压力, 过冷) ---
    # 先找泡点温度
    AS.update(CP.PQ_INPUTS, P_cond, 0.0)
    T_bubble = AS.T()
    
    T3 = T_bubble - subcool_k
    AS.update(CP.PT_INPUTS, P_cond, T3)
    h3 = AS.hmass()

    # --- 点 4: 节流 ---
    h4 = h3

    # ============================
    # 4. 计算 COP
    # ============================
    q_cool = h1 - h4
    w_comp = h2 - h1
    cop = q_cool / w_comp

    print(f"\n[计算结果]")
    print(f"h1 (吸气): {h1/1000:.2f} kJ/kg")
    print(f"h2 (排气): {h2/1000:.2f} kJ/kg (排气温度: {T2-273.15:.2f}°C)")
    print(f"h3 (液体): {h3/1000:.2f} kJ/kg")
    print("-" * 30)
    print(f"制冷量 : {q_cool/1000:.2f} kJ/kg")
    print(f"耗功量 : {w_comp/1000:.2f} kJ/kg")
    print(f"理论极限 COP: {cop:.4f}")

if __name__ == "__main__":
    calculate_r454b_cop_robust(7.2, 46.1, 5.0, 5.0)