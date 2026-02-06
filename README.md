# A function plotter in python

A recreational programming project.

The idea is to implement a simple math expression language and simple features to plot functions.

For now a simple matplotlib based implementation is provided.

Example:

```
from plotter.matplotlib import plot_expression

plot_expression("abs(sin(x)) + (5 * exp(-100*x^2) * cos(x))", start=-7, stop=7, increment=0.001)
```

![Function plotted in the [-7.0, 7.0] range with 0.001 increments](./plot_example.png)
