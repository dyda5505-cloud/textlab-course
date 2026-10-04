FROM alpine:3.22
RUN apk add --no-cache bash curl coreutils file
ARG STUDENT=Student
ENV STUDENT=$STUDENT
COPY run.sh /usr/local/bin/run-lab
RUN chmod +x /usr/local/bin/run-lab
CMD ["bash", "/usr/local/bin/run-lab"]
