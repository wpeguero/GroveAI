FROM python:3.10.5
#To prune the system just use docker system prune -a

RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD ./models/tclass_VGG4/ /app/models/tclass_VGG4/
ADD pipeline.py /app/
ADD capapp.py /app/
ENTRYPOINT [ "python" ]
CMD ["gunicorn", "-w 4", "-b 127.0.0.1:8080", "myproject:capapp"]