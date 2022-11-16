import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dashcc
import dash_html_components as dashhtml
from dash.dependencies import Input, Output
import pymysql


offenders_by_sex = pd.read_csv("https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/CVA08/CSV/1.0/en")
offenders_by_age = pd.read_csv("https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/CVA09/CSV/1.0/en").fillna(0)
recorded_offences = pd.read_csv("https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/RCD03/CSV/1.0/en")

#Assignment Part 2
#Part 1 is below Part 2
######################################################################################################
mylist=[]
for sort_direction in [False, True]:
    for i in ["Male", "Female"]:
        x = pd.DataFrame(offenders_by_sex[offenders_by_sex["Sex of Suspected Offender"] == i]).reset_index()
        y = x.groupby(["ICCS Offence Group", "Sex of Suspected Offender"])["VALUE"].sum().reset_index()
        z = y.sort_values("VALUE", ascending=sort_direction).head(3).reset_index()
        x = z.nlargest(3, "VALUE").loc[:, ["Sex of Suspected Offender" ,"ICCS Offence Group", "VALUE"]]
        records = x.to_records(index=False)
        for r in records:
            mylist.append(r)
try:
    db = pymysql.connect(host='mydb.ckdp24lnc1eb.eu-west-1.rds.amazonaws.com', port=3306,
                         user='jl28pepsi',
                         password='kongstrong100')
    cursor =db.cursor()
    sql = '''drop database if exists mydatabase'''
    cursor.execute(sql)
    sql = '''create database mydatabase'''
    cursor.execute(sql)
    cursor.connection.commit()
    sql = '''use mydatabase'''
    cursor.execute(sql)
    cursor.execute('''DROP TABLE IF EXISTS crimes''')
    db.commit()
    cursor.execute('''CREATE TABLE crimes(Sex text,Crime text,Total text)''')
    db.commit()
    sql = '''INSERT INTO crimes(Sex,Crime,Total) VALUES ('%s','%s','%s')'''
    for i in mylist:
        cursor.execute('''INSERT INTO crimes(Sex,Crime,Total) VALUES ('%s','%s','%s')''' % (i[0], i[1], i[2]))
        db.commit()
    sql = '''SELECT * FROM crimes'''
    cursor.execute(sql)
    print(cursor.fetchall())
    db.close()

except Exception as e:
    print(e)
##################################################################################################################

#Assignment Part 1
app = dash.Dash()
application = app.server
app.layout = dashhtml.Div(
    children=[
        dashhtml.Div(
            children=[
                dashhtml.H1(
                    children="CS3204 - Crime Analytics", style={'textAlign': 'center'}, className="header-title"
                ),
                dashhtml.H2(
                    children="Analysis of Data of Suspected Offenders of Recorded Crime Incidents in Ireland 2018-2020",
                    className="header-description", style={'textAlign': 'center'},
                ),
            ],
            className="header", style={'backgroundColor': 'blue'},
        ),

        dashhtml.Div(
            children=[
                dashhtml.Div(children='Year', style={'fontSize': "15px"}, className='menu-title'),
                dashcc.Dropdown(
                    id='year-filter',
                    options=[
                        {'label': Year, 'value':Year}
                        for Year in offenders_by_sex.Year.unique()
                    ],
                    value=2018,
                    clearable=False,
                    searchable=False,
                    className='dropdown'
                ),
            ],
            className='menu',
        ),
        dashhtml.Div(
            children=dashcc.Graph(
                id='barchart'
                    ),
            style={'width': '50%', 'display': 'inline-block'},
                ),
        dashhtml.Div(
            children=dashcc.Graph(
                id='piechart',
            ),
            style={'width': '50%', 'display': 'inline-block'},
        ),
        dashhtml.Div(
            children=dashcc.Graph(
                id='scatterplot'
            ),
            style={'width': '50%', 'display': 'inline-block'}),
        dashhtml.Div(
            children=dashcc.Graph(
                id='grouped_barchart',
            ),
            style={'width': '50%', 'display': 'inline-block'})
            ],
)

@app.callback(
    Output("barchart", "figure"),
    [Input("year-filter", "value")],
)
def update_barchart(Year):
    filtered_data = offenders_by_sex[offenders_by_sex["Year"] == Year]
    bar = px.bar(
        filtered_data,  # dataframe
        y=filtered_data["ICCS Offence Group"].unique(),
        x=filtered_data[filtered_data["Sex of Suspected Offender"] == "Both sexes"]["VALUE"],
        labels={"x": "Total Recorded", "y": "ICCS Offence Group"},
        color=filtered_data[filtered_data["Sex of Suspected Offender"] == "Both sexes"]["VALUE"],
        text=filtered_data[filtered_data["Sex of Suspected Offender"] == "Both sexes"]["VALUE"],
        orientation='h')
    bar.update_layout(margin=dict(l=200, r=20, t=50, b=20))
    bar.update_traces(texttemplate="%{text:.2s}")
    return bar

@app.callback(
    Output("piechart", "figure"),
     [Input("year-filter", "value")])
def update_piechart(Year):
    filtered_data1 = offenders_by_sex[offenders_by_sex["Year"] == Year]
    filtered_data2 = filtered_data1[filtered_data1["Sex of Suspected Offender"] != "Both sexes"]
    piechart = px.pie(filtered_data2, names="Sex of Suspected Offender", values="VALUE",
                      title='Offences by Sex')
    return piechart

@app.callback(
    Output("scatterplot", "figure"),
    [Input("year-filter", "value")],)
def update_scatterplot(Year):
    filtered_data = offenders_by_age[offenders_by_age["Year"] == Year]
    filtered_data1 = filtered_data[filtered_data["Age of Suspected Offender at Time of Offence"] != "All ages"]
    scatter = px.scatter(filtered_data1, y="Age of Suspected Offender at Time of Offence", x="ICCS Offence Group",
    size="VALUE",color="VALUE", title="Offences by Age Group and ICCS Offence Group")
    scatter.update_layout(xaxis_tickangle=30, title=dict(x=0.5),xaxis_tickfont=dict(size=10),
            yaxis_tickfont=dict(size=10), paper_bgcolor="LightSteelblue")
    scatter.update_layout(margin=dict(l=100, r=70, t=30, b=120))
    return scatter

@app.callback(
    Output("grouped_barchart", "figure"),
    [Input("year-filter", "value")])
def update_grouped_barchart(Year):
    filtered_data = recorded_offences[recorded_offences["Year"] == Year]
    figure = px.bar(filtered_data, x="Garda Region", y="VALUE",color='Detection Status', barmode='group',
                    title="Offences by Detection Status and Region")
    return figure

if __name__ == '__main__':
    application.run(debug=True, port=8080)