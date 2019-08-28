import flask

from app import parking

app = flask.Flask("parking_rates")


@app.route("/load", methods=["POST"])
def load():
    payload = flask.request.json
    parking.load_mgr(payload)
    return flask.jsonify({'saved': True}), 200


@app.route("/query", methods=["GET"])
def query():
    begin_str = flask.request.json['begin']
    end_str = flask.request.json['end']
    result = parking.query_mgr(begin_str, end_str)
    return flask.jsonify({'rate': result}), 200

