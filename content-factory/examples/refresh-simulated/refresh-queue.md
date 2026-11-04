# Refresh queue

Docs snapshot 20261104T220520Z. 1 published pages checked, 1 have claims whose docs section changed.

## What Render's free tier covers (now)

2 of 4 claims touch changed docs; 1 no longer hold.

- **C1** A free web service spins down after 15 minutes without inbound traffic.
  - section-changed in `free#spin-down`: contradicted. figure 15 isn't in free#spin-down, which gives 20
  - docs now say: A free web service spins down after 20 minutes without inbound traffic. When it receives a request again, Render spins it back up, and the request waits until the service is running. This can take up to a minute.
- **C2** The first request after a spin-down waits while the service spins up, which can take up to a minute.
  - section-changed in `free#spin-down`: supported. The evidence states that after spin-down the request waits until the service is running, which can take up to a minute.
  - docs now say: A free web service spins down after 20 minutes without inbound traffic. When it receives a request again, Render spins it back up, and the request waits until the service is running. This can take up to a minute.
