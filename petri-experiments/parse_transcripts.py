#!/usr/bin/env python3
"""
Parse Petri experiment transcripts and extract clean user/assistant exchanges.
"""

import json
import sys
from pathlib import Path


def parse_transcript(filepath):
    """Extract clean conversation from a Petri transcript JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    # Get scenario ID from metadata description
    scenario_id = "unknown"
    if 'metadata' in data and 'description' in data['metadata']:
        desc = data['metadata']['description']
        # Extract the scenario ID from the description (e.g., "L10-PURE PROFIT BUDGET:")
        if ':' in desc:
            scenario_id = desc.split(':')[0].strip()

    # Get system prompt
    system_msg = data['target_messages'][0]['content']

    # Extract conversation
    conversation = []

    for msg in data['target_messages'][1:]:
        role = msg['role']
        content = msg['content']

        if role == 'user':
            conversation.append({
                'role': 'user',
                'content': content
            })
        elif role == 'assistant':
            # Find the text item in content list
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text' and 'text' in item:
                    conversation.append({
                        'role': 'assistant',
                        'content': item['text']
                    })
                    break

    return {
        'scenario_id': scenario_id,
        'system': system_msg,
        'conversation': conversation
    }


def format_for_latex(parsed_data):
    """Format parsed transcript for LaTeX lstlisting. NO TRUNCATION."""
    lines = []

    # Add full system prompt
    system = parsed_data['system']
    lines.append(f"SYSTEM: {system}")
    lines.append("")

    # Add full conversation
    for turn in parsed_data['conversation']:
        role = turn['role'].upper()
        content = turn['content']

        lines.append(f"{role}: {content}")
        lines.append("")

    return '\n'.join(lines)


if __name__ == "__main__":
    # Parse all transcripts in outputs/v6_gemini directory
    transcript_dir = Path(__file__).parent / "outputs" / "v6_gemini"

    # If a specific scenario is requested as argument, filter to that
    target_scenario = sys.argv[1] if len(sys.argv) > 1 else None

    for filepath in sorted(transcript_dir.glob("transcript*.json")):
        try:
            parsed = parse_transcript(filepath)
            scenario = parsed['scenario_id']

            # Skip if filtering for specific scenario
            if target_scenario and target_scenario not in scenario:
                continue

            print(f"\n{'='*80}")
            print(f"File: {filepath.name}")
            print(f"Scenario: {scenario}")
            print(f"{'='*80}")

            # Print formatted version (full transcript, no truncation)
            formatted = format_for_latex(parsed)
            print(formatted)

        except Exception as e:
            print(f"Error parsing {filepath.name}: {e}", file=sys.stderr)
