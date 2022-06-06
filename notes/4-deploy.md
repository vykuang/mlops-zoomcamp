# Model Deployment

## Batch vs Online

Determine the requirement of the end-user. Can they afford to wait for results, or is realtime required?

### Batch

Model could regularly pull data from DB, run model, evaluate

* Customer churn could be on a monthly basis
* Ride duration may be require half-hour update basis, so customers have a semi-up to date information on whether they should bother.



Usually 1 to 1 client-server relationship

### Web service

### Streaming

Typically 1-to-many relation between pipeline and data consumer

Once a ride has started, data could be streamed to multiple services:

1. Tip prediction
2. ride duration (more accurate version using more finely grained data)



Another example with video streaming, in particular content moderation. User uploading a video is an event in a streaming pipeline that could trigger the following services:

1. copyright violation
2. NSFW
3. violence

Decisions from each of those services could stream to another pipeline, consumed by a centralized decision service.

Services could be added above that also feeds into the centralized decision service, to provide another point of data on whether the video should be removed or not.
