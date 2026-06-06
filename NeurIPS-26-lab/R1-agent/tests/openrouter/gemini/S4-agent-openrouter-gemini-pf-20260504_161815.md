/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/targets/python_pocketflow/S4-agent-openrouter-gemini.py:37: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  with DDGS() as ddgs:
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/targets/python_pocketflow/S4-agent-openrouter-gemini.py:37: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  with DDGS() as ddgs:
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/targets/python_pocketflow/S4-agent-openrouter-gemini.py:37: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  with DDGS() as ddgs:
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/targets/python_pocketflow/S4-agent-openrouter-gemini.py:37: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  with DDGS() as ddgs:
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/targets/python_pocketflow/S4-agent-openrouter-gemini.py:37: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  with DDGS() as ddgs:

Status     : complete
Iterations : 5

Answer:
Based on the information available, here is an overview of **PocketFlow**, its purpose, and instructions for installation.

### What is PocketFlow?
**PocketFlow** is an open-source framework developed by **Tencent AI Lab** designed to automate the compression and acceleration of deep learning models. 

Its primary goal is to take large, computationally expensive neural networks and make them small and efficient enough to run on mobile devices (like smartphones) or embedded systems without significantly sacrificing accuracy. It achieves this through several automated techniques, including:
*   **Channel Pruning:** Removing redundant neurons or layers.
*   **Weight Quantization:** Reducing the precision of the network's weights (e.g., from 32-bit floating point to 8-bit integers).
*   **Model Distillation:** Training a smaller "student" model to mimic a larger "teacher" model.
*   **Multi-GPU Training:** Support for accelerating the compression process itself.

---

### How to Install PocketFlow
PocketFlow is primarily built to work with **TensorFlow** (specifically versions 1.x) and requires a Linux environment (Ubuntu is recommended).

#### 1. Prerequisites
Ensure you have the following installed on your system:
*   Python 3.5 or 3.6
*   TensorFlow (GPU version recommended: `tensorflow-gpu==1.10.0` or higher within the 1.x range)
*   CUDA Toolkit and cuDNN (compatible with your TensorFlow version)
*   CMake (3.2 or higher)

#### 2. Clone the Repository
Open your terminal and clone the official GitHub repository:
```bash
git clone --recursive https://github.com/Tencent/PocketFlow.git
cd PocketFlow
```

#### 3. Install Dependencies
It is highly recommended to use a virtual environment (like `conda` or `virtualenv`) to avoid version conflicts:
```bash
pip install -r requirements.txt
```

#### 4. Build Custom Operators
PocketFlow uses some custom C++ operators that need to be compiled:
```bash
# Navigate to the specific layer directory if necessary (e.g., quantization layers)
# Run the provided compilation scripts
sh (path_to_script)/build.sh
```

#### 5. Verify Installation
You can test the installation by running one of the provided example scripts for a standard dataset like CIFAR-10:
```bash
python learn.py --cfg cifar10_resnet20_distillation.json
```

### Important Usage Note
As of 2024, PocketFlow is no longer actively maintained by Tencent and is specifically optimized for **TensorFlow 1.x**. If you are using modern TensorFlow 2.x or PyTorch, you may encounter compatibility issues. For newer projects, researchers often look at alternatives like the *TensorFlow Model Optimization Toolkit* or *NVIDIA TensorRT*.
