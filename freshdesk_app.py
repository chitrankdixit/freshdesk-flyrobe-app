__author__ = 'py'

from flask import Flask, request, json
from flask_restful import Resource, Api
#from sqlalchemy import create_engine
from json import dumps
#from flask.ext.jsonify import jsonify
import re
import requests
from freshdesk.api import API

a = API('flyrobe.freshdesk.com', 'TDLf4uy3QM7YEqMrWHo0', version=2)

app = Flask(__name__)
api = Api(app)

@app.route('/test/')
def test():
    return "Its working , Yay"

@app.route('/fetch/ticket/v1/')
def data():
    # here we want to get the value of order_id (i.e. ?order_id=some-value)
    order_id = request.args.get('order_id')

    g = a.tickets.list_open_tickets()
    data = g.json()

    for each in data:
        order_id_list = each["custom_fields"]["cf_proforma_invoice_id"].split(";")
        if order_id in order_id_list:
            #call freshdesk api to filter ticket based on proforma_invoice_id
            requests.get('https://flyrobe.freshdesk.com/api/v2/search/tickets?query = "custom_fields["cf_proforma_invoice_id] = each["custom_fields"]["cf_proforma_invoice_id"]"', auth=('TDLf4uy3QM7YEqMrWHo0', 'test'))

    return "Tickets generated successfully"

@app.route('/escalation/push/v1/')
def conversation():
    ticket_id = request.args.get('id')
    ticket = a.tickets.get_ticket(ticket_id)
    conv = requests.get('https://flyrobe.freshdesk.com/api/v2/tickets/57862/conversations', auth=('TDLf4uy3QM7YEqMrWHo0', 'test'))
    conv_data = conv.json()
    counter = 1
    for each in conv_data:
        if each["support_email"] != 'support@flyrobe.freshdesk.com':
            counter += 1
    if counter >= 3:
        ticket = a.tickets.update_ticket(ticket_id, group_id = 9000169467)

    return "Pushed to escalation"


@app.route('/fetch/proforma/v1/')
def ticket_data():
    ticket_id = request.args.get('id')
    ticket_current = a.tickets.get_ticket(int(ticket_id))
    regex = '[MmFf][A-Za-z][RrEe]\s*?([0-9]){6}[A-Za-z]?[0-9]?[0-9]?'
    search_string = ticket_current.description + ticket_current.description_text + ticket_current.subject
    matched = re.finditer(regex, search_string)
    ticket_current.order_id = []
    if matched:
        while True:
            try:
                val = matched.__next__().group()
                # eliminate the child code
                if len(val) > 9:
                    val = val[0:9]
                ticket_current.order_id.append(val.upper())
            except StopIteration:
                break
    ticket_current.order_id = list(set(ticket_current.order_id))
    ticket_current.custom_fields["cf_proforma_invoice_id"] = ";".join(ticket_current.order_id)
    if not ticket_current.custom_fields["cf_proforma_invoice_id"]:
        ticket_current = a.tickets.update_ticket(ticket_current.id,
                                custom_fields = {"cf_proforma_invoice_id" : ticket_current.custom_fields['cf_proforma_invoice_id']})

    return "The post is succussful"

if __name__ == '__main__':
    app.run(debug=True)

    # if each['order_id'] == []:
    #     each['custom_fields']['cf_proforma_invoice_id'] = "EMPTY"
    #     ticket = request.tickets.update_ticket(each['id'],
    #                              custom_fields={'cf_proforma_invoice_id': each['custom_fields']['cf_proforma_invoice_id']})
    #
    # else:
    # each['custom_fields']['cf_proforma_invoice_id'] = ";".join(each['order_id'])
    # ticket = request.tickets.update_ticket(each['id'],
    #                              custom_fields={'cf_proforma_invoice_id': each['custom_fields']['cf_proforma_invoice_id']})
    #

