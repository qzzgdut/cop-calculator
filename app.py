from flask import Flask, render_template, request, jsonify
from cop_cal import calculate_scroll_cop

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    
    try:
        result = calculate_scroll_cop(
            refrigerant=data['refrigerant'],
            t_evap_c=float(data['t_evap_c']),
            t_cond_c=float(data['t_cond_c']),
            superheat_k=float(data.get('superheat_k', 5)),
            subcooling_k=float(data.get('subcooling_k', 5)),
            is_efficiency=float(data.get('is_efficiency', 0.80)),
            motor_efficiency=float(data.get('motor_efficiency', 0.93))
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    # host='0.0.0.0' allows access from other devices on the same network
    app.run(host='0.0.0.0', debug=True, port=5001)
