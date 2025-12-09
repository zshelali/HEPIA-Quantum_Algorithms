# QOTP Usage:

> [!WARNING]
> Only tested with Python 3.10.18 and 3.10.19

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

You can also use pyenv.

2. Install requirements (make sure that you are at the root of the project):

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Run the experiment:

```bash
python qotp/pipe.py
```

The result of the calculation should be $(x + y) \bmod 4$.

You can verify the result by checking `images/histogram.png`.
The results are in binary.

You can also take a look at the circuit at `images/final_circuit.png`.

To try another calculation, you can edit the last line in `pipe.py`:

```python
adder_pipe(2, 1, debug_mode=False)
```

Here we calculate $(2 + 1) \bmod 4 = 3$.

As we only use two qubits per input, one should only use 2-bit numbers.

You can also find some example outputs in `qotp/example_outputs`.
