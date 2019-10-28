###################
# Import packages #
###################

import json, requests, os, smtplib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import six
from datetime import datetime, date
from IPython.display import Javascript, display, HTML
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders

#####################################
# Remove previous .jpgs from folder #
#####################################

for file in os.listdir():
    if file.endswith('.jpg'):
        os.remove(file)

##################
# Obtain upflags #
##################

params = (
    ('AlertType', 'XXX'),
    ('Email', 'XXX'),    
    ('Segment', False)
)

# Access API

response = requests.get("https://analytics.algodynamix.com/v1/pi/GetRealTimeStatus", verify = False, params=params, auth=('XXX', 'XXX'))
upflags = []
returns = []
for item in json.loads(response.text):
    last_flag = pd.DataFrame.from_dict(item['flags'][0], orient='index').T
    last_price = pd.DataFrame.from_dict(item['m1Quotes'][0], orient='index').T['close']
    
    last_flag = pd.concat([last_flag, last_price], axis=1)
    
    # Convert UNIX time object to regular format
    last_flag['dts'] = datetime.fromtimestamp(last_flag.dts.values[0]/1000).strftime('%d-%m-%Y %H:%M')
    last_flag['days'] = (datetime.today() - datetime.strptime(last_flag.dts.values[0], '%d-%m-%Y %H:%M')).days
    returns.append(str(round(((last_flag.close[0] - last_flag.price[0]) / last_flag.close[0]) * 100,3)) + "%")
    
    upflags.append(list(last_flag.iloc[0]))
returns = pd.DataFrame(returns, columns=['Returns'])
upflags = pd.DataFrame(upflags, columns=['Flag issued since', 'Type', 'Flag price', 'Instrument', 'Last Price', 'Number of days'])
upflags = pd.concat([upflags, returns], axis=1)
upflags = upflags[['Instrument', 'Flag issued since', 'Number of days', 'Type', 'Flag price', 'Last Price', 'Returns']]
upflags['Instrument'] = upflags['Instrument'].map({'AEX': 'AEX', 'FESX': 'EURO STOXX 50', 'ES': 'S&P 500'})

try:
    open_upflags = upflags.loc[upflags['Type'] == 'Up']
except:
    open_upflags = "No current up flags available"
    
####################
# Obtain downflags #
####################

params = (
    ('AlertType', 'XXX'),
    ('Email', 'XXX'),    
    ('Segment', False)
)

# Access API

response = requests.get("https://analytics.algodynamix.com/v1/pi/GetRealTimeStatus", verify = False, params=params, auth=('XXX', 'XXX'))
downflags = []
returns = []
for item in json.loads(response.text):
    last_flag = pd.DataFrame.from_dict(item['flags'][0], orient='index').T
    last_price = pd.DataFrame.from_dict(item['m1Quotes'][0], orient='index').T['close']
    
    last_flag = pd.concat([last_flag, last_price], axis=1)
    
    # Convert UNIX time object to regular format
    last_flag['dts'] = datetime.fromtimestamp(last_flag.dts.values[0]/1000).strftime('%d-%m-%Y %H:%M')
    last_flag['days'] = (datetime.today() - datetime.strptime(last_flag.dts.values[0], '%d-%m-%Y %H:%M')).days
    returns.append(str(round(((last_flag.price[0] - last_flag.close[0]) / last_flag.price[0]) * 100,3)) + "%")
    
    downflags.append(list(last_flag.iloc[0]))
returns = pd.DataFrame(returns, columns=['Returns'])
downflags = pd.DataFrame(downflags, columns=['Flag issued since', 'Type', 'Flag price', 'Instrument', 'Last Price', 'Number of days'])
downflags = pd.concat([downflags, returns], axis=1)
downflags = downflags[['Instrument', 'Flag issued since', 'Number of days', 'Type', 'Flag price', 'Last Price', 'Returns']]
downflags['Instrument'] = downflags['Instrument'].map({'AEX': 'AEX', 'FESX': 'EURO STOXX 50', 'ES': 'S&P 500'})

try:
    open_downflags = downflags.loc[downflags['Type'] == 'Down']
except:
    open_downflags = "No current down flags available"

##################################################### 
# Convert tables to images and store output as .jpg #
#####################################################

def render_mpl_table(data, col_width="auto", row_height=1, font_size=13,
                     header_color='#15218f', row_colors=['#f1f1f2', '#f1f1f2'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
    plt.savefig(filename, bbox_inches='tight', pad_inches=0, dpi=300)

filename = "openupflags.jpg"
if open_upflags is not "No current up flags available":
    render_mpl_table(open_upflags, header_columns=0, col_width=2.5)

filename = "opendownflags.jpg"
if open_downflags is not "No current down flags available":
    render_mpl_table(open_downflags, header_columns=0, col_width=2.5)

###################
#  Compose email  #
###################

receiver_email = ['example@example.com']

msgRoot = MIMEMultipart('related')
msgRoot['Subject'] = 'Overview'
msgRoot['From'] = 'XXX' 
msgRoot['To'] = ", ".join(receiver_email)

msgAlternative = MIMEMultipart('alternative')
msgRoot.attach(msgAlternative)

msgText = MIMEText('Error')
msgAlternative.attach(msgText)

if open_upflags is not "No current up flags available" and open_downflags is not "No current down flags available":
    
    msgText = MIMEText('INSERT HTML CODE', 'html')
    msgAlternative.attach(msgText)
    fp = open('ouf.jpg', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

    fp = open('odf.jpg', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image2>')
    msgRoot.attach(msgImage)
    
if open_upflags is not "No current up flags available" and open_downflags is "No current down flags available":
    
    msgText = MIMEText('INSERT HTML CODE', 'html')
    msgAlternative.attach(msgText)
    fp = open('ouf.jpg', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)
    
if open_upflags is "No current up flags available" and open_downflags is not "No current down flags available":
    
    msgText = MIMEText('INSERT HTML CODE', 'html')
    msgAlternative.attach(msgText)
    fp = open('odf.jpg', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

if open_upflags is "No current up flags available" and open_downflags is "No current down flags available":
    
    msgText = MIMEText('INSERT HTML CODE', 'html')
    msgAlternative.attach(msgText)
    
server = smtplib.SMTP('smtp@server.com', 25)
server.connect("smtp@server.com", 25)
server.sendmail('sender@example.com' , 'receiver@example.com' , msgRoot.as_string())
server.quit()
