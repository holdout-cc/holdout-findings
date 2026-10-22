# run from the repo root
from resources_servers.single_step_tool_use_with_argument_comparison.common.verification_utils import (
    ActionComparator, ToolCallComparatorConfig)

expected = 'cd /workspace/numpy__numpy__ && python -c "import numpy; numpy.test()" 2>&1 | head -30'
for threshold in (0.0, 0.1):
    cmp = ActionComparator(config=ToolCallComparatorConfig(word_count_similarity_threshold=threshold))
    print(threshold, cmp._compare_strings(expected, "echo done", None))
