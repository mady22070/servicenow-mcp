# Contributing to ServiceNow MCP

Thank you for your interest in contributing to ServiceNow MCP! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
- Use the [GitHub Issues](https://github.com/mady22070/servicenow-mcp/issues) page
- Search existing issues before creating a new one
- Provide detailed information including:
  - ServiceNow version and instance type
  - Python version and operating system
  - Steps to reproduce the issue
  - Expected vs actual behavior
  - Relevant logs or error messages

### Suggesting Features
- Open a [GitHub Discussion](https://github.com/mady22070/servicenow-mcp/discussions) for feature requests
- Describe the use case and expected behavior
- Consider if the feature fits the project's scope and goals

### Code Contributions

#### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/mady22070/servicenow-mcp.git
cd servicenow-mcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

#### Making Changes
1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Make your changes**: Follow the coding standards below
3. **Test your changes**: Run tests and ensure they pass
4. **Commit your changes**: Use clear, descriptive commit messages
5. **Push and create PR**: Submit a pull request with detailed description

## 📝 Coding Standards

### Python Style
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 88 characters (Black default)

### Code Quality
- Write clear, self-documenting code
- Add docstrings to all public functions and classes
- Use type hints for function parameters and return values
- Handle errors gracefully with appropriate exception handling

### Testing
- Write unit tests for new functionality
- Maintain or improve test coverage
- Test with multiple ServiceNow versions when possible
- Include integration tests for complex features

### Documentation
- Update relevant documentation for changes
- Add docstrings following Google style
- Include usage examples for new features
- Update API reference documentation

## 🏗️ Project Structure

### Adding New Packs
When adding new functional areas:

1. **Create pack module**: `servicenow_mcp/packs/your_pack.py`
2. **Follow pack pattern**:
   ```python
   """
   Your Pack - Description of functionality
   """
   
   def your_function(client, param1, param2, dry_run=False):
       """Function description with clear parameters"""
       # Implementation
       return result
   ```
3. **Register tools**: Add to `tool_registry.py`
4. **Add tests**: Create `tests/test_your_pack.py`
5. **Update documentation**: Add to API reference

### Adding New Tools
For individual tools:

1. **Use decorators**: Apply appropriate decorators for error handling
2. **Follow naming**: Use clear, descriptive function names
3. **Parameter validation**: Validate required parameters
4. **Error handling**: Return consistent error format
5. **Documentation**: Include comprehensive docstrings

## 🧪 Testing Guidelines

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_query_pack.py

# Run with coverage
python -m pytest --cov=servicenow_mcp

# Run integration tests (requires ServiceNow instance)
python -m pytest tests/integration/
```

### Test Structure
- **Unit tests**: Test individual functions in isolation
- **Integration tests**: Test with actual ServiceNow instances
- **Mock tests**: Use mocks for external dependencies
- **Fixtures**: Create reusable test data and configurations

### Test Requirements
- All new code should have corresponding tests
- Tests should be independent and repeatable
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

### PR Description
Include in your pull request:
- **Summary**: Brief description of changes
- **Motivation**: Why this change is needed
- **Changes**: Detailed list of modifications
- **Testing**: How the changes were tested
- **Breaking Changes**: Any backwards compatibility issues

### Review Process
1. **Automated checks**: CI/CD pipeline runs tests and linting
2. **Code review**: Maintainers review code quality and design
3. **Testing**: Changes are tested in development environment
4. **Documentation**: Ensure documentation is complete and accurate
5. **Merge**: Approved changes are merged to main branch

## 🔒 Security Guidelines

### Sensitive Information
- Never commit credentials or API keys
- Use environment variables for configuration
- Sanitize logs to remove sensitive data
- Follow principle of least privilege

### Code Security
- Validate all inputs from external sources
- Use parameterized queries to prevent injection
- Handle authentication and authorization properly
- Follow ServiceNow security best practices

## 📚 Resources

### ServiceNow Documentation
- [ServiceNow REST API](https://docs.servicenow.com/bundle/vancouver-application-development/page/integrate/inbound-rest/concept/c_RESTAPI.html)
- [ServiceNow Scripting](https://docs.servicenow.com/bundle/vancouver-application-development/page/script/server-scripting/concept/c_ServerSideScripting.html)
- [ServiceNow Best Practices](https://docs.servicenow.com/bundle/vancouver-application-development/page/build/applications/concept/c_ApplicationDevelopmentBestPractices.html)

### MCP Resources
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

### Development Tools
- [Python Testing](https://docs.python.org/3/library/unittest.html)
- [Black Code Formatter](https://black.readthedocs.io/)
- [isort Import Sorter](https://pycqa.github.io/isort/)

## 🎯 Development Priorities

### High Priority
- Performance optimizations
- Additional ServiceNow module support
- Enhanced error handling and logging
- Comprehensive test coverage

### Medium Priority
- Advanced workflow automation
- Machine learning integration
- GraphQL API support
- Custom app scaffolding

### Low Priority
- UI enhancements
- Additional output formats
- Extended documentation
- Community integrations

## 💬 Communication

### Getting Help
- **GitHub Discussions**: General questions and community support
- **GitHub Issues**: Bug reports and feature requests
- **Code Reviews**: Technical discussions on pull requests

### Community Guidelines
- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow the project's code of conduct

## 🏆 Recognition

Contributors are recognized in:
- **README.md**: Major contributors listed
- **CHANGELOG.md**: Contributions noted in releases
- **GitHub**: Contributor statistics and graphs
- **Releases**: Special thanks in release notes

Thank you for contributing to ServiceNow MCP! Your efforts help make ServiceNow automation more accessible and powerful for everyone.