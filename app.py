from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
from otp import genotp
from cmail import send_mail
from stoken import entoken,dntoken
import mysql.connector
from mysql.connector import (connection)
from io import BytesIO
import flask_excel as excel
import re
mydb=connection.MySQLConnection(user='root',host='localhost',password='admin',database='notes')
app=Flask(__name__)
app.secret_key='code@123'
excel.init_excel(app)

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/userregister',methods=['GET','POST'])
def userregister():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        useremail=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(user_email) from users where user_email=%s',[useremail])
        email_count=cursor.fetchone()
        if email_count[0]==0:
            gotp=genotp()
            userdata={'useremail':useremail,'username':username,'password':password,'gotp':gotp}
            subject='OTP fo SNM Application'
            body=f'Use the given otp {gotp}'
            send_mail(to=useremail,body=body,subject=subject)
            flash(f'OTP has been sent to {useremail}')
            return redirect(url_for('otpverify',endata=entoken(data=userdata))) #passing encrypted otp
        elif email_count[0]==1:
            flash(f'{useremail} already existed pls login')
            return redirect(url_for('userregister'))
        else:
            flash('something went wrong')

    return render_template('register.html')

@app.route('/otpverify/<endata>',methods=['GET','POST'])
def otpverify(endata):
    if request.method=='POST':
        user_otp=request.form['otp']
        dndata=dntoken(data=endata) #decrypting the otp
        if dndata['gotp']==user_otp:
            cursor=mydb.cursor()
            cursor.execute('insert into users(username,user_email,password) values(%s,%s,%s)',[dndata['username'],dndata['useremail'],dndata['password']])
            mydb.commit()
            cursor.close()
            flash(f'details registered successfully')
            return 'success'
        else:
            flash('otp was incorrect')
    return render_template('otp.html')

@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if request.method=='POST':
        login_useremail=request.form['useremail']
        login_password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where user_email=%s',[login_useremail])
        email_count=cursor.fetchone()
        if email_count[0]==1:
            cursor.execute('select password from users where user_email=%s',[login_useremail])
            stored_password=cursor.fetchone()
            if stored_password[0]==login_password:
                #adding session
                session['user'] = login_useremail
                return redirect(url_for('dashboard'))
            else:
                flash('password is incorrect')
                return redirect(url_for('userlogin'))
        elif email_count[0]==0:
            flash(f'{login_useremail} not found')
            return redirect(url_for('userlogin'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('pls login first')

@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['note-title']
            description = request.form['note-description']
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from users where user_email=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('insert into notes(title,description,added_by) values(%s,%s,%s)',[title,description,user_id[0]])
                mydb.commit()
                flash('notes added successfully')
                return redirect(url_for('dashboard'))
            else:
                flash('user id not found')
                return redirect(url_for('addnotes'))
        else:
            flash('could not store data')
            return redirect(url_for('dashboard'))
    else:
        flash('please login first')
        return redirect(url_for('userlogin'))

    #return render_template('addnotes.html')

@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where added_by=(select userid from users where user_email=%s)',
        [session.get('user')])
        all_notesdata=cursor.fetchall()
        print(all_notesdata)
        if all_notesdata:
            return render_template('dashboard.html',all_notesdata=all_notesdata)
        else:
            flash('Could not fetch notes data')
            return redirect(url_for('dashboard'))
    else:
        flash('pls login to view all notes')
        return redirect(url_for('dashboard'))
    
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from notes where nid=%s',[nid])
        notes_data = cursor.fetchone()
        if notes_data:
            return render_template('viewnotes.html',notes_data=notes_data)
        else:
            flash('could not fetch notes data')
            return redirect(url_for('viewallnotes'))
    else:
        flash('pls login to view notes')
        return redirect(url_for('userlogin'))

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('delete from notes where nid=%s',[nid])
        mydb.commit()
        #notes_data = cursor.fetchone()
        flash('Note deleted successfully')

        return redirect(url_for('viewallnotes'))
    else:
        flash('pls login to view notes')
        return redirect(url_for('userlogin'))
    
@app.route('/updatenotes/<nid>', methods=['GET', 'POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)

        if request.method == 'POST':
            new_title = request.form['title']
            new_description = request.form['description']
            cursor.execute('UPDATE notes SET title=%s,description=%s WHERE nid=%s', [new_title,new_description, nid])
            mydb.commit()
            flash(f'Description for note {nid} updated successfully')
            return redirect(url_for('viewallnotes'))

    # GET request: fetch note data to pre-fill the form
    cursor.execute('SELECT * FROM notes WHERE nid=%s', [nid])
    notes_data = cursor.fetchone()

    if notes_data:
        return render_template('update.html', notes_data=notes_data)
    else:
        flash('Note not found')
        return redirect(url_for('viewallnotes'))
        
@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
    if session.get('user'):
        if request.method=='POST':
            file_data = request.files['file-upload']
            # print(file_data.filename)
            # print(file_data.read())
            fname = file_data.filename
            f_data = file_data.read()
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from users where user_email=%s',[session.get('user')])
            user_id = cursor.fetchone()
            cursor.execute('insert into files(filename,file_data,added_by) values(%s,%s,%s)',[fname,f_data,user_id[0]])
            mydb.commit()
            cursor.close()
            flash('file added successfully')
            return redirect(url_for('dashboard'))
    else:
        flash('pls login to upload file') 
        return redirect(url_for('userlogin'))

@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fid,filename,created_at from files where added_by=(select userid from users where user_email=%s)',[session.get('user')])
        all_filesdata=cursor.fetchall()
        print(all_filesdata)
        if all_filesdata:
            return render_template('dashboard.html',all_filesdata=all_filesdata)
        else:
            flash('Could not fetch files data')
            return redirect(url_for('dashboard'))
    else:
        flash('pls login to view all files')
        return redirect(url_for('dashboard'))
    
@app.route('/viewfiles/<fid>')
def viewfiles(fid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select fid,filename,file_data,created_at from files where fid=%s and added_by=(select userid from users where user_email=%s)',[fid,session.get('user')])
        files_data = cursor.fetchone()
        bytes_array = BytesIO(files_data[2])
        return send_file(bytes_array,download_name=files_data[1],as_attachment=False)
    else:
        flash('pls login to view file')
        return redirect(url_for('userlogin'))

@app.route('/downloadfiles/<fid>')
def downloadfiles(fid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select fid,filename,file_data,created_at from files where fid=%s and added_by=(select userid from users where user_email=%s)',[fid,session.get('user')])
        files_data = cursor.fetchone()
        bytes_array = BytesIO(files_data[2])
        return send_file(bytes_array,download_name=files_data[1],as_attachment=True)
    else:
        flash('pls login to view file')
        return redirect(url_for('userlogin'))

@app.route('/deletefiles/<fid>')
def deletefiles(fid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select userid from users where user_email=%s',[session.get('user')])
        user_id = cursor.fetchone()
        cursor.execute('delete from files where fid=%s and added_by=%s',[fid,user_id[0]])
        mydb.commit()
        flash('File deleted successfully')

        return redirect(url_for('viewallfiles'))
    else:
        flash('pls login to view files')
        return redirect(url_for('userlogin'))

@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select userid from users where user_email=%s',[session.get('user')])
        user_id = cursor.fetchall()
        cursor.execute('select * from notes where added_by=%s',user_id[0])
        notes_data = cursor.fetchall()
        data = [list(i) for i in notes_data]
        col_heading = ['Notes_id','Title','Description','Note_created_time','Added_by']
        data.insert(0,col_heading)
        return excel.make_response_from_array(data,'xlsx',file_name = 'data')
    else:
        flash('to get excel data pls login first')
        return redirect(url_for('userlogin'))

@app.route('/search',methods=['POST'])
def search():
    if session.get('user'):
        if request.method == 'POST':
            searchdata = request.form['sdata']
            string = ['A-Za-z0-9']
            pattern = re.compile(f'^{string}',re.IGNORECASE)
            if re.match(pattern,searchdata):
                cursor = mydb.cursor(buffered=True)
                cursor.execute("select * from notes where title like %s or description like %s or created_at like %s or nid like %s",[searchdata+'%',searchdata+'%',searchdata+'%',searchdata+'%'])
                search_result = cursor.fetchall()
                cursor.execute("select * from files where filename like %s or created_at like %s",[searchdata+'%',searchdata+'%'])
                search_result2 = cursor.fetchall()
                if search_result or search_result2:
                    return render_template('dashboard.html',search_result=search_result,search_result2=search_result2)
                else:
                    flash('no search found')
                    return redirect(url_for('dashboard'))
            else:
                flash(f'pls give some value in search')
                return redirect(url_for('dashboard'))
    else:
        flash('to search data pls login')
        return redirect(url_for('userlogin'))
    
@app.route('/logout')
def logout():
    if session.get('user'):
        return render_template('welcome.html')
app.run(debug=True,use_reloader=True)