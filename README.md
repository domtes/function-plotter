# A function plotter in python

A recreational programming project.

The idea is to implement a simple math expression language and simple features to plot functions.

For now a simple matplotlib based implementation is provided.

Example:

```
from plotter.matplotlib import plot_expression

plot_expression("sin(x) * 2^(3*x)", start=-10.0, stop=10.0, increment=0.1)
```

![Function plotted in the [-10.0, 10.0] range with 0.1 increments](./plot_example.png)
