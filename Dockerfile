FROM python:3.7

WORKDIR /app

COPY requirements.txt /app/
COPY ./ /app

RUN make docker_build

RUN pip3.7 install -r requirements.txt
RUN pip3.7 install dist/planets-*.whl

EXPOSE 8080

CMD ["planets-serve"]