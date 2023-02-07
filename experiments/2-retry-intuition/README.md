# Experiments to get an intuition about how retry mechansim works

This experiments is going to be presented in a meeting with David, Bradley, Johan , and Cristian on Feb 1st. 

The experiments consist of generating the traffic to a diamond application with various retry parameters and a static circuit breaker configuration. In general the architecture looks like:

```mermaid
flowchart LR;
    A("Traffic Generator <br/> (HTTPMon)") --> B(Diamond application);
    subgraph ide1 [Diamond application]
    B(<font color=black>Service1) <--> C(<font color=black>Service2)
    B(<font color=black>Service1) <--> D(<font color=black>Service3)
    B(<font color=black>Service1) <--> E(<font color=black>Service4)
    C(<font color=black>Service2) <--> F(<font color=black>Service5)
    D(<font color=black>Service3) <--> F(<font color=black>Service5)
    E(<font color=black>Service4) <--> F(<font color=black>Service5)


    style B fill:#00FF00
    style C fill:#00FF00
    style D fill:#00FF00
    style E fill:#00FF00

    style F fill:#ffaf7a

    end
```

In the above architecture, the `second service` is more complex than the `first service` in terms of processing time per requests. The `first service` requires `0.01 ms` while the `second service` requires `5ms` time to process the requests. 