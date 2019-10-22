# Examples for using Katana as a Python module

In general, there are four steps to getting the Katana module up and running:

1. Create a Monitor object (either one of the defaults, or subclass your own).
2. Create a Manager object, passing your monitor to the constructor.
3. Start the manager analysis.
4. Queue a target for evaluation.

After all targets are queued, you can use the `Manager.join` method to wait for completion.