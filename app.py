import base64
import json
import requests
import tensorflow as tf
import os
import sys
import numpy as np
import io

from flask import Flask, request, render_template
from .data_augmentation import *


app = Flask(__name__)

project_root = os.path.dirname(os.path.abspath(__file__))


##################################################################################
#                                                                                #
#                        INIT EQUATION SOLVER MODEL                              #
#                                                                                #
##################################################################################

MODEL_DIR    = project_root + '/saved_model'
CLASS_NAMES  = ['+', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '=', '*']

model = None

print("INFO: Project root located at {}".format(project_root), file=sys.stdout)
print("INFO: Model directory located at {}".format(MODEL_DIR), file=sys.stdout)
    
# Loads model from directory
model = tf.keras.models.load_model(MODEL_DIR)
if model is None:
    print("ERROR: Model was none. Unable to load tensorflow model", file=sys.stderr)
else:
    print("INFO: Model successfully loaded", file=sys.stdout)


def make_predictions(model_input):
    model_output = model.predict(model_input)

    eqn_list = []
    for pred in model_output:
        pred_class = CLASS_NAMES[np.argmax(pred)]
        eqn_list.append(pred_class)
        eqn = "".join(eqn_list)
    solution = eval(eqn)
    return eqn, solution


##################################################################################
#                                                                                #
#                            FLASK APP ENDPOINTS                                 #
#                                                                                #
##################################################################################

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    eqn, solution = '', ''
    status_code = 404

    if request.method == 'POST':
        try:
            data = request.get_data()
            decoded_bytes = base64.decodebytes(data)

            buffer_data = np.frombuffer(decoded_bytes, np.int8)
            input_image = cv2.imdecode(buffer_data, 0)
            model_input = get_augmented_data(np.array(input_image))

            eqn, solution = make_predictions(model_input)

            status_code = 200
            print(f"INFO: The equation is {eqn} and the answer is {solution}", file=sys.stdout)

        except Exception as e:
            print("ERROR: {}".format(e))

    return json.dumps({ 'status': status_code, 'equation': eqn, 'solution': solution })


@app.route('/test', methods=['GET'])
def test():
    eqn, solution = '', ''
    status_code = 404

    try:
        test_data = get_test_data()
        eqn, solution = make_predictions(test_data)

        status_code = 200
        print(f"INFO: The equation is {eqn} and the answer is {solution}", file=sys.stdout)

    except Exception as e:
        print("ERROR: {}".format(e))

    return json.dumps({ 'status': status_code, 'equation': eqn, 'solution': solution })


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')


