# Deploy for free

Render offers free instance types for web services, Render Postgres, and Render Key Value, for hobby projects and testing.

## Spin-down behavior {#spin-down}

A free web service spins down after 20 minutes without inbound traffic. When it receives a request again, Render spins it back up, and the request waits until the service is running. This can take up to a minute.

## Unsupported features {#unsupported}

Background workers, private services, and cron jobs aren't available on the free instance type. Free web services can't scale beyond one instance.

## Ephemeral filesystem {#filesystem}

Free instances can't attach a persistent disk. Any file a free service writes at runtime is lost when the service redeploys or spins down.

## Free Postgres {#postgres}

A free Render Postgres database expires 30 days after it's created. Upgrade it to a paid instance type before then to keep your data.
