# Scientific Methodology Guidelines

## Experiment Design Principles
- Start simple, iterate to complexity
- Always use proper train/validation splits
- Track all metrics systematically
- Save experiment data as numpy arrays

## Code Requirements
All generated experiment code must:
- Be single-file, self-contained Python scripts
- Include explicit GPU handling with device detection:
  ~~~python
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  print(f'Using device: {device}')
  ~~~
- Properly normalize model inputs
- Save results to `working_dir/experiment_data.npy`
- Complete within the configured timeout

## Evaluation Standards
- Report validation loss at each epoch
- Track defined evaluation metrics
- Generate visualizations for all results
- Never hallucinate or fabricate data

## Data Saving Convention
~~~python
experiment_data = {
    'dataset_name': {
        'metrics': {'train': [], 'val': []},
        'losses': {'train': [], 'val': []},
        'predictions': [],
        'ground_truth': [],
    }
}
np.save(os.path.join(working_dir, 'experiment_data.npy'), experiment_data)
~~~
