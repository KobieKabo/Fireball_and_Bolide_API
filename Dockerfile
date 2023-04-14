

FROM python:3.8.10 

RUN pip install Flask==2.2.2

RUN pip install requests==2.26.0

RUN pip install xmltodict==0.12.0

RUN pip install geopy==2.3.0

RUN pip install DateTime==5.0

RUN pip install pyyaml==6.0

COPY fireball_api.py /fireball_api.py

CMD ["python", "/fireball_api.py"]
