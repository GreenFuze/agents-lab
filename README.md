# MetaFFI Multi-Agent System

A comprehensive multi-agent system designed specifically for MetaFFI plugin development, build system management, and cross-language interoperability tasks.

## 🏗️ System Architecture

### Hierarchical Agent Structure

```
MetaFFI Root Coordinator
├── Build System Agent Hierarchy
│   ├── BuildSystemAgent (Core build analysis)
│   ├── BuildScriptFixer (Script fixes)
│   └── AdvancedBuildFixer (Complex parsing fixes)
├── Plugin Development Agent Hierarchy
│   └── PluginDevelopmentAgent (Plugin analysis & development)
├── Test System Agent Hierarchy
│   └── TestSystemAgent (CTest & testing framework)
└── Development Execution Agent Hierarchy
    └── DevelopmentExecutionAgent (Implementation coordination)
```

## 🚀 Features

### Core Capabilities
- **Hierarchical Task Routing**: Intelligent task distribution to specialized agents
- **Smart Model Pool**: Dynamic model switching based on agent requirements
- **LM Studio Integration**: Automatic model loading/unloading via LM Studio API
- **State Persistence**: Full crash recovery with automatic state saving
- **Security Controls**: All tools restricted to MetaFFI root directory
- **Escalation System**: Hierarchical escalation to human when needed
- **Comprehensive Analysis**: Multi-phase analysis of entire MetaFFI system

### Agent Specializations
- **Build System**: CMake analysis, script fixing, compilation issues
- **Plugin Development**: Language plugin analysis, architecture review
- **Test System**: CTest integration, test execution, framework analysis
- **Advanced Parsing**: Complex target parsing, Ninja output handling
- **Model Pool Management**: Intelligent model switching based on task complexity

## 📋 Requirements

### System Requirements
- Windows 11 (tested)
- 32GB RAM recommended
- NVIDIA GPU with 8GB VRAM (for LM Studio)
- Python 3.8+

### Dependencies
```bash
pip install -r requirements.txt
```

### MetaFFI Environment
- MetaFFI installed at `C:\src\github.com\MetaFFI`
- Available plugins: c, go, openjdk, python311
- CMake and build tools available

## 🎯 Usage

### Command Line Interface

```bash
# Run comprehensive analysis (default)
python main.py

# Specific tasks
python main.py build          # Build system analysis
python main.py fix           # Apply script fixes
python main.py advanced      # Advanced parsing fixes
python main.py plugin        # Plugin development analysis
python main.py test          # Test system analysis
python main.py execute       # Development execution
python main.py comprehensive # Full system analysis

# Model pool and system status
python main.py models        # Model pool status
python main.py status        # System status
python main.py hierarchy     # Agent hierarchy

# Interactive mode
python main.py interactive

# Recovery mode
python main.py recovery
```

### Interactive Mode Commands

```
1. build        - Run build system analysis
2. fix          - Apply fixes to build scripts
3. advanced     - Apply advanced parsing fixes
4. plugin       - Analyze plugin development
5. test         - Analyze test system
6. execute      - Development execution coordination
7. comprehensive - Run comprehensive analysis of all systems
8. hierarchy    - Display agent hierarchy
9. status       - Show system status
10. models      - Show model pool status
11. recovery    - Show recovery options
12. quit        - Exit
```

## 🔧 Configuration

### Smart Model Pool Configuration (`config.py`)
```python
# LM Studio Configuration
LMSTUDIO_CONFIG = {
    "base_url": "http://127.0.0.1:1234",
    "api_base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio"
}

# Smart Model Pool - Different models for different complexity levels
MODEL_POOL = {
    "coordinator": {
        "model_name": "qwen2.5-vl-7b-instruct",
        "use_cases": ["root_coordination", "complex_analysis", "human_escalation"],
        "temperature": 0.7,
        "max_tokens": 4096
    },
    "specialist": {
        "model_name": "qwen2.5-vl-7b-instruct", 
        "use_cases": ["build_analysis", "plugin_development", "testing"],
        "temperature": 0.8,
        "max_tokens": 2048
    },
    "executor": {
        "model_name": "qwen2.5-vl-7b-instruct",
        "use_cases": ["script_fixes", "simple_analysis", "validation"],
        "temperature": 0.6,
        "max_tokens": 1024
    }
}

# Agent Model Assignment Strategy
AGENT_MODEL_STRATEGY = {
    "RootCoordinator": "coordinator",
    "BuildSystemAgent": "specialist", 
    "BuildScriptFixer": "executor",
    "AdvancedBuildFixer": "specialist",
    "PluginDevelopmentAgent": "specialist",
    "TestSystemAgent": "specialist",
    "DevelopmentExecutionAgent": "coordinator"
}
```

### Agent Configuration
- **Access Levels**: read_only, development, full
- **Confidence Threshold**: 0.7 minimum for task execution
- **State Auto-save**: Every 30 seconds
- **Tool Restrictions**: MetaFFI root directory only

## 📊 System Status

### Current Implementation Status
- ✅ Complete hierarchical agent system (7 agents)
- ✅ Smart Model Pool with LM Studio integration
- ✅ Dynamic model switching based on agent requirements
- ✅ State persistence and crash recovery
- ✅ Comprehensive task routing
- ✅ Security controls and access management
- ✅ MetaFFI tool integration
- ✅ Interactive and command-line interfaces
- ✅ Comprehensive analysis capabilities

### Agent Status
- **RootCoordinator**: ✅ Fully operational
- **BuildSystemAgent**: ✅ Fully operational
- **BuildScriptFixer**: ✅ Fully operational
- **AdvancedBuildFixer**: ✅ Fully operational
- **PluginDevelopmentAgent**: ✅ Fully operational
- **TestSystemAgent**: ✅ Fully operational
- **DevelopmentExecutionAgent**: ✅ Fully operational

## 🔄 Recovery System

The system includes comprehensive crash recovery:

### State Persistence
- Automatic state saving every 30 seconds
- Timestamped state files in `agent_states/`
- Full agent context and task progress preservation

### Recovery Options
```bash
# View recovery options
python main.py recovery

# Interactive recovery selection
python main.py interactive
# Choose option 11 (recovery)
```

### Recovery Data
- Agent state and hierarchy
- Task progress and context
- Tool access permissions
- Error states and escalations

## 🧪 Testing

### Build System Testing
```bash
# Test build scripts
python main.py build

# Test script fixes
python main.py fix

# Test advanced parsing
python main.py advanced
```

### Plugin Development Testing
```bash
# Analyze plugins
python main.py plugin

# Check plugin architecture
python main.py comprehensive
```

### Test System Testing
```bash
# Run test analysis
python main.py test

# Full system test
python main.py comprehensive
```

## 🔍 Troubleshooting

### Common Issues

1. **Access Denied Errors**
   - Check MetaFFI root path configuration
   - Verify agent access levels
   - Review security restrictions

2. **Model Connection Issues**
   - Verify LM Studio is running
   - Check model configuration in `config.py`
   - Ensure model is loaded in LM Studio

3. **Environment Issues**
   - Check virtual environment activation
   - Verify MetaFFI installation
   - Review build tool availability

4. **State Recovery Issues**
   - Check `agent_states/` directory permissions
   - Verify state file integrity
   - Use fresh start if needed

### Debug Mode
```bash
# Enable verbose logging
export METAFFI_DEBUG=1
python main.py comprehensive
```

## 📈 Performance

### System Performance
- **Comprehensive Analysis**: ~2-3 minutes
- **Individual Tasks**: 30-60 seconds
- **State Persistence**: <1 second
- **Agent Communication**: <100ms

### Resource Usage
- **Memory**: ~2-4GB (depending on model)
- **VRAM**: 8GB (qwen2.5-vl-7b-instruct)
- **CPU**: Moderate (inference dependent)
- **Disk**: <100MB (state files)

## 🛠️ Development

### Adding New Agents
1. Inherit from `BaseMetaFFIAgent`
2. Implement required methods
3. Add to `RootCoordinator` hierarchy
4. Update task routing

### Extending Functionality
1. Add new tools to `tools/metaffi_tools.py`
2. Update agent methods
3. Add command-line options
4. Update documentation

## 📄 License

This project is part of the MetaFFI ecosystem. See MetaFFI license for details.

## 🤝 Contributing

1. Follow the hierarchical agent pattern
2. Maintain security restrictions
3. Add comprehensive testing
4. Update documentation
5. Ensure state persistence compatibility

## 📞 Support

For issues related to:
- **Agent System**: Check agent logs and state files
- **MetaFFI Integration**: Verify MetaFFI installation
- **Model Issues**: Check LM Studio configuration
- **Build Problems**: Review build system logs

---

**MetaFFI Multi-Agent System** - Specialized agents for cross-language interoperability development.
