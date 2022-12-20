import json
from datetime import datetime
from csv import reader
from kafka import KafkaProducer


def parse_and_publish(line, producer):
    """
    Takes a line of a csv, generates a dictionary, and then publishes it to Kafka topic.

    :param line: CSV line
    :param producer: Instantiated KafkaProducer
    """
    post_fields = [
        'id', 'time', 'url', 'score', 'num_cmts'
    ]
    msg = dict(zip(post_fields, line))
    producer.send('reddit', msg)


def run_fill():
    """
    Builds a KafkaProducer, processes news.csv, passing it to Redpanda
    """
    producer = KafkaProducer(
        bootstrap_servers='redpanda:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    with open('news.csv') as file:
        csv_reader = reader(file)
        for line in csv_reader:
            line[1] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            parse_and_publish(line, producer)


if __name__ == "__main__":
    run_fill()
