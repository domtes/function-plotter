import matplotlib.pyplot as plt

from .parser import eval_in_range


def plot_expression(
    expression: str,
    start: float = 0.0,
    stop: float = 1.0,
    increment: float = 0.1,
):
    fig, ax = plt.subplots()
    domain, values = eval_in_range(expression, start, stop, increment)
    ax.grid(
        visible=True, which="both", color="lightgray", linestyle="--", linewidth=0.5
    )
    ax.plot(domain, values)

    ax.legend((expression,))

    plt.show()
