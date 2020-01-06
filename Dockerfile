FROM python:3.7

COPY requirements.txt /build/requirements.txt
RUN pip3 install setuptools==42.0.2 --upgrade \
 && pip3 install -r /build/requirements.txt

COPY . /build
RUN cd /build \
 && python3 setup.py install \
 && rm -rf /build

EXPOSE 8080
RUN example-init
CMD uvicorn example.server:app
