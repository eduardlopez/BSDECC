from flask import Flask, request, render_template
import sys
import json

app = Flask(__name__)

ms = {}
wallys = []

@app.route('/', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        print("REQUEST:"+str(request.data), file=sys.stderr)
        ms = json.loads(request.data.decode("utf-8"))
        wallys.insert(0,ms)
        print("REQUEST:" + str(wallys), file=sys.stderr)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return render_template("wally_template.html",wallys=wallys)