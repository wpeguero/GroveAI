FROM python:3.10.5
#To prune the system just use docker system prune -a

RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD ./models/tclass_VGG4/ /app/models/tclass_VGG4/
ADD pipeline.py /app/
ADD capapp.py /app/
#ENTRYPOINT [ "python" ]
EXPOSE 8050
CMD "gunicorn capapp:server -b :8050"