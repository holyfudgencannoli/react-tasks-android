from flask import Flask, request, jsonify, send_from_directory, current_app
from flask_cors import CORS
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, DateTime, create_engine, MetaData, Table
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import Config
from datetime import datetime


app = Flask(__name__, static_folder='local_frontend')
app.config.from_object(Config)
# CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://10.0.0.45:5173"]}}, supports_credentials=True)

Base = declarative_base()


engine = create_engine(Config.DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    due_datetime = Column(String)
    log_datetime = Column(String)
    fin_datetime = Column(String)
    completed = Column(Boolean, default=False)
    memo = Column(String)


    def to_dict(self):
        return{
            'id': self.id,
            'name': self.name,
            'due_datetime': self.due_datetime,
            'log_datetime': self.log_datetime,
            'fin_datetime': self.fin_datetime,
            'completed': self.completed,
            'memo': self.memo,
        }


Base.metadata.create_all(bind=engine)


@app.route('/')
def home_page():
    return send_from_directory(current_app.static_folder, "index.html")

@app.route('/task-records')
def task_records_page():
    return send_from_directory(current_app.static_folder, "index.html")

@app.route('to-do-list')
def to_do_list_page():
    return send_from_directory(current_app.static_folder, "index.html")


@app.route('/api/log-tasks', methods=['POST'])
def log_task():
    db_session = SessionLocal()

    data = request.form

    name = data.get('name')
    due_datetime = data.get('due_datetime')
    log_datetime = data.get('log_datetime')
    fin_datetime = data.get('fin_datetime')
    completed = data.get('completed')
    memo = data.get('memo')

    new_task = Task(
        name=name,
        due_datetime=due_datetime,
        log_datetime=log_datetime
    )

    db_session.add(new_task)
    db_session.commit()

    new_task_dict = new_task.to_dict()
    db_session.close()


    return jsonify({'success': True, 'task': new_task_dict})


@app.route('/api/get-tasks-all', methods=['GET'])
def get_tasks_all():
    db_session = SessionLocal()

    tasks = db_session.query(Task).all()

    tasks_serialized = [t.to_dict() for t in tasks]
    db_session.close()
    return jsonify({'tasks': tasks_serialized})

@app.route('/api/get-tasks', methods=['POST'])
def get_tasks():
    data = request.get_json()

    date_str = data.get('date')

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    db_session = SessionLocal()

    tasks = []
    for t in db_session.query(Task).all():
        if t.log_datetime: 
            try:
                task_date = datetime.fromisoformat(t.log_datetime).date()
                if task_date == target_date:
                    tasks.append(t.to_dict())
            except ValueError:
                # optionally log invalid date strings
                print("Skipping invalid datetime:", t.log_datetime)
    db_session.close()

    return jsonify({'tasks': tasks})

@app.route('/api/get-tasks-to-do', methods=['GET'])
def get_tasks_to_do():
    db_session = SessionLocal()

    tt = db_session.query(Task).filter_by(completed=False).all()

    tasks = []
    for t in tt:
        tasks.append(t.to_dict())
    db_session.close()

    return jsonify({'tasks': tasks})

@app.route('/api/mark-complete', methods=['POST'])
def mark_complete():
    data = request.get_json()

    task_id = data.get('task_id')

    db_session = SessionLocal()

    task_obj = db_session.query(Task).filter_by(id=task_id).first() #type:ignore


    task_obj.completed = True
    task_obj.fin_datetime = datetime.now().isoformat()
    print(datetime.now().isoformat())

    db_session.commit()
    db_session.close()

    return jsonify({'message': 'Task marked complete!'})




if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
