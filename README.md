# System Design Learning 🎓

An interactive collection of system design concepts and data structures with beautiful terminal-based demonstrations. Learn fundamental computer science topics through hands-on experimentation and visualization.

## 🌟 What's Inside

### Data Structures & Algorithms
- **🌸 Bloom Filter Demo** - Understand probabilistic data structures with interactive bit array visualization
- **📚 Inverted Index Demo** - Explore document indexing and search algorithms used by search engines
- **⏰ Rate Limiter Demo** - Learn rate limiting with leaky bucket and token bucket algorithms

### Distributed Systems
- **💬 WebSocket Chat System** - Multi-server distributed chat with inter-server communication
- **🎯 Real-time Message Routing** - See how messages route across server networks

### Interactive Learning Tools
- **🎮 TicTacToe** - Classic game implementation
- **⏱️ Clock Simulator** - Time-based system simulation

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/system-design-learning.git
cd system-design-learning

# Install dependencies
pip install -r requirements.txt

# Run any demo
python3 bloom_filter_demo.py
```

## 📖 Demos

### Bloom Filter Demonstrator
```bash
python3 bloom_filter_demo.py
```
- Interactive bit array visualization
- Real-time false positive probability calculation
- Configurable hash functions and array sizes
- Step-by-step insertion and lookup animations

![Bloom Filter Demo](docs/bloom-filter-preview.png)

### Inverted Index Demonstrator
```bash
python3 inverted_index_demo.py
```
- Document indexing and search functionality
- Term frequency analysis
- Search result ranking
- Real-time index visualization

### Rate Limiter Demonstrator
```bash
python3 rate_limiter_demo.py
```
- Leaky bucket and token bucket algorithms
- Live request processing visualization
- Configurable rates and capacities
- Request drop/accept statistics

### Distributed WebSocket Chat
```bash
# Launch the interactive demo
python3 websocket_demo.py

# Or start individual components
python3 websocket_server.py --port 8000 --name Server1
python3 websocket_client.py
```
- Multi-server architecture
- Cross-server message routing
- Real-time client communication
- Server interconnection management

## 🎯 Learning Objectives

### Bloom Filters
- Understand probabilistic data structures
- Learn about space-time tradeoffs
- Explore hash function properties
- Grasp false positive concepts

### Inverted Indices
- Document indexing fundamentals
- Search algorithm optimization
- Term frequency and ranking
- Full-text search principles

### Rate Limiting
- Traffic control mechanisms
- Algorithm comparison (leaky vs token bucket)
- System capacity planning
- Request queuing strategies

### Distributed Systems
- Server-to-server communication
- Message routing in networks
- Connection management
- Fault tolerance concepts

## 🛠️ Technical Details

### Dependencies
- **Rich** - Beautiful terminal interfaces and visualizations
- **WebSockets** - Real-time communication for distributed demos
- **Inquirer** - Interactive command-line prompts
- **Matplotlib/NumPy** - Data visualization support

### System Requirements
- Python 3.7+
- Terminal with color support
- Network access for WebSocket demos

## 🎨 Features

- **Rich Terminal UI** - Beautiful, interactive command-line interfaces
- **Real-time Visualization** - See algorithms work step-by-step
- **Educational Focus** - Designed for learning with clear explanations
- **Hands-on Experimentation** - Configurable parameters and scenarios
- **History Tracking** - Review operations and understand patterns

## 📚 How to Use

1. **Start with Basics** - Begin with bloom filter or inverted index demos
2. **Experiment** - Try different configurations and parameters
3. **Read Explanations** - Each demo includes detailed algorithm explanations
4. **Progress to Advanced** - Move on to distributed systems demos
5. **Build Understanding** - Use the interactive features to deepen comprehension

## 🤝 Contributing

Contributions are welcome! Whether you want to:
- Add new system design concepts
- Improve existing demonstrations
- Fix bugs or enhance documentation
- Suggest new learning modules

Please feel free to open issues or submit pull requests.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🎓 Educational Use

Perfect for:
- Computer science students learning system design
- Software engineers preparing for technical interviews
- Developers wanting to understand fundamental algorithms
- Anyone curious about how large-scale systems work

## 🔗 Related Resources

- [Designing Data-Intensive Applications](https://dataintensive.net/)
- [System Design Interview Questions](https://github.com/donnemartin/system-design-primer)
- [High Scalability Blog](http://highscalability.com/)

---

⭐ **Star this repo if it helps you learn system design concepts!** ⭐