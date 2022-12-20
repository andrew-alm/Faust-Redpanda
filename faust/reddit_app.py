from datetime import datetime, timedelta
import uuid
import faust

# Define Faust App
app = faust.App(
    'redditapp',
    broker='kafka://redpanda:9092'
    #
)


# Define incoming post data
class Posts(faust.Record, serializer='json', isodates=True):
    id: str
    time: datetime
    url: str
    score: int
    num_cmts: int


# Define Master Dataset post
class MPosts(faust.Record, serializer='json'):
    id: str
    time: datetime
    url: str
    score: int
    num_cmts: int
    uuid: str


# Define Processed Post
class ProcPosts(faust.Record, serializer='json'):
    avg_score: float
    min_score: float
    max_score: float
    avg_cmts: float
    max_cmts: float
    min_cmts: float


# Define topics
topic_input = app.topic('reddit', value_type=Posts, key_type=bytes)
topic_master = app.topic('master-dataset', value_type=MPosts)
topic_processed = app.topic('reddit-stats', value_type=ProcPosts)

# Define table logic
async def windowing_func(key, stream):
    """
    Events passed in based on the tumbling window will have some basic statistics
    calculated on them. Currently state is stored in memory, but could be expanded
    with RocksDB. User would just need to add it in the Docker image and then
    add it to the

    :param events: Set of events in the tumbling window
    """
    timestampe = key[1][0]
    score = [float(event.score) for event in stream]
    num_cmts = [float(event.num_cmts) for event in stream]

    print('Inside')
    topic_processed.send_soon(
        value=ProcPosts(
            avg_score=sum(score) / len(score),
            min_score=min(score),
            max_score=max(score),
            avg_cmts=sum(num_cmts) / len(num_cmts),
            max_cmts=max(num_cmts),
            min_cmts=min(num_cmts)
        ),
        key='Reddit-Statistics'
    )

ftable = (
    app.Table(
        'avg-count-values',
        default=list,
        key_type=str,
        value_type=Posts,
        on_window_close=windowing_func,
        partitions=1
    ).tumbling(
        size=5,
        key_index=True,
        expires=timedelta(seconds=5)
    ).relative_to_field(Posts.time)
)

# Finally create the direct application logic
@app.agent(topic_input)
async def task(stream):
    """
    This function takes events as they land on the reddit topic, and then
    append them with a UUID. They are then pushed to the master-database
    topic and then kafkaconnect pushes them to S3.

    :param events: Faust app events (connection to redpanda topic)
    :yields: event: Single processed JSON

        id: str
    time: datetime
    url: str
    score: int
    num_cmts: int
    uuid: str
    """
    async for event in stream:
        updated_event = event.asdict()
        updated_event['score'] = int(updated_event['score'])
        updated_event['num_cmts'] = int(updated_event['num_cmts'])
        updated_event['uuid'] = uuid.uuid4()

        await topic_master.send(key=bytes('Master-Dataset', 'utf-8'), value=MPosts.from_data(updated_event))


@app.agent(topic_input)
async def task2(stream):
    async for event in stream:
        value_list = ftable["events"].value()
        value_list.append(event)
        ftable["events"] = value_list

if __name__ == "__main__":
    app.main()