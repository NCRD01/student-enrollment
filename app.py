from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy

#flask
app = Flask(__name__)
app.secret_key = "secretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"
db = SQLAlchemy(app)

#stores users into database (students and teachers)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    name = db.Column(db.String(100))
    role = db.Column(db.String(20))

#stores course information
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True) #course ID
    name = db.Column(db.String(100)) #course name
    teacher = db.Column(db.String(100)) #course teacher
    time = db.Column(db.String(100)) #course times
    capacity = db.Column(db.Integer) #course capacity
    enrollments = db.relationship("Enrollment", backref="course") #number of enrollments

#allows students to enroll into classes 
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    grade = db.Column(db.Integer)

#login page and redirect to pages based on login information
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            session["user_id"] = user.id
            session["role"] = user.role

            if user.role == "student":
                return redirect("/student")
            elif user.role == "teacher":
                return redirect("/teacher")

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

#logout button
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#student page
@app.route("/student")
def student():
    user = User.query.get(session["user_id"])
    courses = Course.query.all()
    enrolled = Enrollment.query.filter_by(student_id=user.id).all()
    enrolled_ids = [e.course_id for e in enrolled]

    return render_template(
        "student.html",
        user=user,
        courses=courses,
        enrolled_ids=enrolled_ids
    )

#student add courses
@app.route("/add_course/<int:course_id>")
def add_course(course_id):
    user_id = session["user_id"]

    existing = Enrollment.query.filter_by(
        student_id=user_id,
        course_id=course_id
    ).first()

    if existing:
        return redirect("/student")

    course = Course.query.get(course_id)
    count = Enrollment.query.filter_by(course_id=course_id).count()

    if count < course.capacity:
        enrollment = Enrollment(
            student_id=user_id,
            course_id=course_id,
            grade=0
        )
        db.session.add(enrollment)
        db.session.commit()

    return redirect("/student")

#student drop courses
@app.route("/drop_course/<int:course_id>")
def drop_course(course_id):
    user_id = session["user_id"]

    enrollment = Enrollment.query.filter_by(
        student_id=user_id,
        course_id=course_id
    ).first()

    if enrollment:
        db.session.delete(enrollment)
        db.session.commit()

    return redirect("/student")

#teacher page
@app.route("/teacher")
def teacher():
    user = User.query.get(session["user_id"])

    courses = Course.query.filter_by(
        teacher=user.name
    ).all()

    return render_template(
        "teacher.html",
        user=user,
        courses=courses
    )

#shows teacher class dashboard
@app.route("/course/<int:course_id>", methods=["GET", "POST"])
def course(course_id):
    course = Course.query.get(course_id)
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()

    if request.method == "POST":
        for enrollment in enrollments:
            grade = request.form.get(str(enrollment.id))
            enrollment.grade = int(grade)

        db.session.commit()
        return redirect(url_for("course", course_id=course_id))

    students = []

    for enrollment in enrollments:
        student = User.query.get(enrollment.student_id)
        students.append((enrollment, student))

    return render_template(
        "course.html",
        course=course,
        students=students
    )

###login user information and courses###
def seed_data():
    if User.query.count() == 0:
        users = [
            User(username="student", password="student", name="Student", role="student"),
            User(username="student2", password="student2", name="Student2", role="student"),
            User(username="teacher", password="teacher", name="Teacher", role="teacher")
        ]

        courses = [
            Course(name="Physics 121", teacher="Susan Walker", time="TR 11:00-11:50 AM", capacity=10),
            Course(name="CS 106", teacher="Teacher", time="MWF 2:00-2:50 PM", capacity=10),
            Course(name="Math 101", teacher="Ralph Jenkins", time="MWF 10:00-10:50 AM", capacity=8),
            Course(name="CS 162", teacher="Teacher", time="TR 3:00-3:50 PM", capacity=1)
        ]
        
        db.session.add_all(users)
        db.session.add_all(courses)
        db.session.commit()

        full_class = Course.query.filter_by(name="CS 162").first()
        student2 = User.query.filter_by(username="student2").first()

        enrollment = Enrollment(
            student_id=student2.id,
            course_id=full_class.id,
            grade=90
        )

        db.session.add(enrollment)
        db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()

    app.run(debug=True)