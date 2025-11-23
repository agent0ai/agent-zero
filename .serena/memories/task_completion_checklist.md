# Agent Zero Task Completion Checklist

## Before Starting Development
1. [ ] Check git status and current branch
2. [ ] Pull latest changes from main
3. [ ] Create feature branch if needed
4. [ ] Activate Python environment
5. [ ] Ensure Docker is running (if needed)

## During Development
1. [ ] Follow snake_case naming for Python functions/variables
2. [ ] Follow PascalCase for class names
3. [ ] Place new tools in `/python/tools/`
4. [ ] Place helper functions in `/python/helpers/`
5. [ ] Update prompts in `/prompts/` if needed
6. [ ] Keep tools modular and single-purpose
7. [ ] Handle exceptions appropriately

## Before Committing Code
1. [ ] Test your changes manually
2. [ ] Run any relevant tests from `/tests/`
3. [ ] Check for Python syntax errors
4. [ ] Remove debug print statements
5. [ ] Update documentation if needed
6. [ ] Clean up temporary files

## Testing Checklist
```bash
# Manual testing
python run_ui.py  # Test in UI
python run_cli.py  # Test in CLI

# Run specific tests if modified
python -m pytest tests/[relevant_test].py

# Check for obvious errors
python -c "import python.tools.your_new_tool"
```

## Quality Checks
1. [ ] Code follows existing patterns in codebase
2. [ ] No hardcoded paths or credentials
3. [ ] Error messages are user-friendly
4. [ ] New features documented in comments
5. [ ] Complex logic has inline documentation

## Git Workflow
```bash
# Before committing
git diff  # Review changes
git status  # Check modified files

# Commit with clear message
git add .
git commit -m "feat: description" # or fix:, docs:, refactor:

# Push to remote
git push origin feature/branch-name
```

## Common Areas to Check

### When Adding New Tools
- [ ] Tool class inherits from base Tool
- [ ] Tool has proper execute method
- [ ] Tool handles errors gracefully
- [ ] Tool returns structured response
- [ ] Tool description in class docstring

### When Modifying Prompts
- [ ] Template variables properly formatted
- [ ] Markdown syntax is valid
- [ ] Instructions are clear and specific
- [ ] No conflicting instructions

### When Working with Memory/Knowledge
- [ ] Memory keys are descriptive
- [ ] Knowledge entries properly indexed
- [ ] No sensitive data stored
- [ ] Cleanup of old/unused entries

### When Updating Dependencies
- [ ] Test with new versions
- [ ] Update requirements.txt
- [ ] Check compatibility with Python version
- [ ] Document any breaking changes

## Final Checklist
1. [ ] All tests passing
2. [ ] Code reviewed for style consistency
3. [ ] Documentation updated
4. [ ] No commented-out code blocks
5. [ ] No TODO comments for completed work
6. [ ] Changes work in both UI and CLI mode
7. [ ] Docker container still builds (if applicable)

## Post-Development
1. [ ] Create pull request with description
2. [ ] Link relevant issues
3. [ ] Request review if needed
4. [ ] Monitor CI/CD pipeline results
5. [ ] Address review feedback promptly