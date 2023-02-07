In general the architecture looks like:

```mermaid
flowchart LR;
    A("Traffic Generator <br/> (HTTPMon)") --> B(Two Tier application);
    subgraph ide1 [Two Tier application]
    B(<font color=black>1st </br> service) <--> C(<font color=black>2nd </br> service)
    style B fill:#00FF00
    style C fill:#ffaf7a

    end
```

In the above architecture, the `second service` is more complex than the `first service` in terms of processing time per requests. The `first service` requires `0.01 ms` while the `second service` requires `5ms` time to process the requests. 