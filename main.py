from flask import Flask, request, render_template, send_from_directory, jsonify, abort, redirect, url_for
import os
from werkzeug.utils import secure_filename
#import magic
import urllib.request
from datetime import datetime
import psycopg2
import psycopg2.extras
import env 
#import extract_radiomics
import json

DATABASE = env.DATABASE        # new
DB_USER = env.DB_USER          # new
DB_PASSWORD = env.DB_PASSWORD  # new
DB_HOST = env.DB_HOST          # new
DB_PORT = env.DB_PORT          # new
SERVER_IP = env.SERVER_IP      # updated
SERVER_PORT = env.SERVER_PORT  # updated

IMAGES_URL = 'http://%s:%s/images'%(SERVER_IP,SERVER_PORT)

app = Flask(__name__, static_url_path='')
app.config["IMAGE_FOLDER_PATH"] = 'static/CT'

@app.route("/home", methods=['GET', 'POST']) 
def home():
    query_text1 = '''SELECT * FROM CANCER_TYPE'''                        # new
    con = psycopg2.connect(database=DATABASE, user=DB_USER, 
                password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)   # new
    # print("DATABASE connection established successfully!")
    cur = con.cursor()                                              # new
    cur.execute(query_text1)                                         # new
    cancer_list = cur.fetchall() 

    query_text2 = '''SELECT * FROM FEATURE_CATEGORY'''                        # new                                              # new
    cur.execute(query_text2)                                         # new
    feature_category_list = cur.fetchall()           

    query_tablenames = '''SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name; '''
    cur.execute(query_tablenames)
    tablenames = cur.fetchall()
    print(tablenames)


    error = None
    if request.method == 'POST':

        if request.form['filename'] == '':
            error = 'Error: Please select DICOM to upload'
        elif request.form['ctype'] == 'Select':
            error = 'Error: Select cancer type.'
        elif request.form['patientID'] == '':
            error = 'Error: Input Patient ID'
        else:
            error = 'Upload successful!'

    feature_values = ['']
    if request.method == 'POST':
        selectdata = request.form['selectData']
        if selectdata != 'Select':
            query_text3 = '''SELECT * FROM ''' + selectdata
            cur.execute(query_text3)
            feature_values = cur.fetchall()
    print(feature_values)
    

    result = ['']
    num_fields = 0
    field_names = ['']
    if request.method == 'POST':   
        file = request.form['filename']  
        pID = int(request.form['patientID'])

        print(file)
        print(pID)

        try:
            cur.execute('''INSERT INTO DICOM_PATH 
                (PATIENT_ID, IMGPATH) 
                VALUES ('%i', '%s')''' %(pID, file))
        except: 
            cur.execute('''UPDATE DICOM_PATH 
                (PATIENT_ID, IMGPATH) 
                VALUES ('%i', '%s')''' %(pID, file))

        con.commit()

        CT_files_path = './static/CT/'+ request.form['patientID']
        fileobject = CT_files_path + '/features.csv'
        lesion_center = [256,256, 110] #(x,y,z) assume one ROI per image
        #radfeat=extract_radiomics.main(CT_files_path, lesion_center)
        # if pyradiomics works

        # print(CT_files_path + '/features.csv')

        cur.execute("DROP TABLE IF EXISTS NEW_FEATURES CASCADE") 
        cur.execute('''CREATE TABLE NEW_FEATURES
              (PATIENT_ID     INT PRIMARY KEY     NOT NULL,
              CONTRAST    DECIMAL                NOT NULL,
              CORRELATION     DECIMAL                NOT NULL,
              SUM_AVERAGE   DECIMAL                NOT NULL,
              ENERGY     DECIMAL                NOT NULL,
              ENTROPY     DECIMAL                NOT NULL,
              HOMOGENEITY     DECIMAL                NOT NULL,
              VARIANCE     DECIMAL                NOT NULL,
              SPHERICITY     DECIMAL                NOT NULL,
              EFFECTIVE_DIAMETER     DECIMAL       NOT NULL);''')
        con.commit()

        #cur = con.cursor()

        with open(fileobject, 'r') as f:
             
        # Skip the header row.
            next(f)
            cur.copy_from(f, 'new_features', sep=',')

        con.commit()

        cur.execute("select * from new_features")
        result = cur.fetchall()
        field_names = [i[0] for i in cur.description]
        num_fields = len(cur.description)


    return render_template('home.html', 
        error = error, 
        cancer_list = cancer_list, 
        feature_category_list = feature_category_list, 
        tablenames = tablenames, 
        result = result,
        field_names = field_names,
        num_fields = num_fields,
        feature_values = feature_values)



@app.route("/databaseupload", methods=['GET', 'POST']) 
def databaseupload():
    
    query_text1 = '''SELECT * FROM CANCER_TYPE'''                        # new
    con = psycopg2.connect(database=DATABASE, user=DB_USER, 
                password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)   # new
    # print("DATABASE connection established successfully!")
    cur = con.cursor()                                              # new
    cur.execute(query_text1)                                         # new
    cancer_list = cur.fetchall()

    error = None
    if request.method == 'POST':
        if request.form['filename'] == '':
            error = 'Error: Please select database to upload'
        elif request.form['ctype'] == 'Select':
            error = 'Error: Select cancer type.'
        else:
            error = 'Upload successful!'

    if request.method == 'POST' and request.form['filename'] != '':
        file = request.form['filename']
        size = len(file)
        table_name = file[:size-4]
        cur.execute("DROP TABLE IF EXISTS " + table_name + "CASCADE") 
        cur.execute("CREATE TABLE " + table_name + "\n"
            '''(PATIENT_ID     INT PRIMARY KEY     NOT NULL,
            CONTRAST    DECIMAL                NOT NULL,
            CORRELATION     DECIMAL                NOT NULL,
            SUM_AVERAGE   DECIMAL                NOT NULL,
            ENERGY     DECIMAL                NOT NULL,
            ENTROPY     DECIMAL                NOT NULL,
            HOMOGENEITY     DECIMAL                NOT NULL,
            VARIANCE     DECIMAL                NOT NULL,
            SPHERICITY     DECIMAL                NOT NULL,
            EFFECTIVE_DIAMETER     DECIMAL       NOT NULL);''')
        con.commit()

        with open(file, 'r') as f:
         
        # Skip the header row.
            next(f)
            cur.copy_from(f, table_name, sep=',')

        con.commit()

    return render_template('databaseupload.html', error=error, cancer_list=cancer_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        id_text = request.form['uname']
        pw_text = request.form['psw']
        type_text = request.form['utype']
        con = psycopg2.connect(database=DATABASE, user=DB_USER, 
                    password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)  
        cur = con.cursor()
        statement = f"SELECT STAFF_ID FROM USERS WHERE STAFF_ID='{id_text}' AND PW = '{pw_text}';"
        cur.execute(statement)
        if not cur.fetchone():  # An empty result evaluates to False.
            error = 'Invalid Credentials. Please try again.'
        elif request.form['utype'] == 'Select':
            error = 'Select User type.'
        elif request.form['utype'] == 'Doctor':
            return redirect(url_for('home'))
        else:
            return redirect(url_for('databaseupload'))
        
        # elif request.form['utype'] == cur.fetchone()[4]:
        #     if request.form['utype'] == 'Doctor':
        #         return redirect(url_for('home'))
        #     else:
        #         return redirect(url_for('databaseupload'))
        # else:
        #     error = 'Invalid User Type'


    return render_template('login.html', error=error)


@app.route('/images/<path:path>')
def get_patient_file(path):
    try:
        return send_from_directory(app.config["IMAGE_FOLDER_PATH"], path)
    except:
        abort(404, description="Image %s not found."%path)


@app.route('/_images_list')
def load_images():
    image_list = [f for f in os.listdir(app.config["IMAGE_FOLDER_PATH"]) if '.jpg' in f]
    return jsonify(image_list = image_list)

app.run(host=SERVER_IP, port=SERVER_PORT)