import os
from pathlib import Path
from typing import Dict, Any
from crewai import Agent, Crew, Process, Task

def write_file(file_path: str, content: str) -> None:
    """Write content to a file, creating directories as needed"""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def run_single_task(agent: Agent, description: str, expected_output: str) -> str:
    """Execute a single task with the given agent"""
    task = Task(description=description, expected_output=expected_output, agent=agent)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return str(result).strip()

def debate_arena(topic: str = 'AI should be open-sourced', 
                max_rounds: int = 3, 
                log_dir: str = 'cookbook/11_debate_arena/logs-spl',
                model: str = 'gemma3') -> Dict[str, Any]:
    """
    CrewAI implementation of the SPL debate_arena workflow.
    Preserves exact workflow logic and prompts from the SPL source.
    """
    
    # Exact prompts from CREATE FUNCTION blocks
    pro_argument_prompt = """You are a skilled debate champion arguing STRONGLY IN FAVOR of the following motion:

Motion: "{topic}"

Your opponent's last argument (or "opening statement" if this is your first turn):
{previous}

Write a focused, persuasive argument supporting the motion. If this is a rebuttal round,
directly address and counter your opponent's points. Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side."""

    con_argument_prompt = """You are a skilled debate champion arguing STRONGLY AGAINST the following motion:

Motion: "{topic}"

Your opponent's last argument (or "opening statement" if this is your first turn):
{previous}

Write a focused, persuasive argument opposing the motion. If this is a rebuttal round,
directly address and counter your opponent's points. Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side."""

    judge_debate_prompt = """You are an impartial debate judge evaluating the following debate.

Motion: "{topic}"

--- PRO SIDE (arguing IN FAVOR) ---
{pro_history}

--- CON SIDE (arguing AGAINST) ---
{con_history}

Evaluate the debate on these criteria:
1. Strength of arguments
2. Quality of rebuttals
3. Clarity and persuasiveness

Declare a winner (PRO or CON) and explain your reasoning in 2-3 paragraphs."""

    try:
        # Initialize variables
        round_count = 0
        pro_history = ''
        con_history = ''
        
        # Create agents with ollama model
        llm_config = f"ollama/{model}"
        
        pro_agent = Agent(
            role="Pro Debater",
            goal="Argue strongly in favor of the given motion",
            backstory="You are a skilled debate champion arguing for the motion.",
            llm=llm_config,
            verbose=False
        )
        
        con_agent = Agent(
            role="Con Debater", 
            goal="Argue strongly against the given motion",
            backstory="You are a skilled debate champion arguing against the motion.",
            llm=llm_config,
            verbose=False
        )
        
        judge_agent = Agent(
            role="Judge",
            goal="Impartially evaluate debate arguments",
            backstory="You are an impartial debate judge.",
            llm=llm_config,
            verbose=False
        )

        print(f'Debate started | topic: {topic} | rounds: {max_rounds}')

        # Opening statements - GENERATE pro_argument(@topic, 'opening statement') INTO @pro
        pro = run_single_task(
            pro_agent,
            pro_argument_prompt.format(topic=topic, previous='opening statement'),
            "A focused, persuasive argument supporting the motion (3-5 paragraphs)"
        )
        
        # GENERATE con_argument(@topic, 'opening statement') INTO @con  
        con = run_single_task(
            con_agent,
            con_argument_prompt.format(topic=topic, previous='opening statement'),
            "A focused, persuasive argument opposing the motion (3-5 paragraphs)"
        )

        # @pro_history := @pro / @con_history := @con
        pro_history = pro
        con_history = con

        print('Opening statements complete')
        
        # CALL write_file(...) INTO NONE
        write_file(f'{log_dir}/opening_pro.md', pro)
        write_file(f'{log_dir}/opening_con.md', con)

        # Rebuttal rounds - WHILE @round < @max_rounds DO
        while round_count < max_rounds:
            print(f'Round {round_count} | pro rebuttal ...')
            
            # GENERATE pro_argument(@topic, @con_history) INTO @pro_rebuttal
            pro_rebuttal = run_single_task(
                pro_agent,
                pro_argument_prompt.format(topic=topic, previous=con_history),
                "A focused rebuttal supporting the motion"
            )
            
            # @pro_history := @pro_history || '\n---\n' || @pro_rebuttal
            pro_history = pro_history + '\n---\n' + pro_rebuttal
            write_file(f'{log_dir}/round_{round_count}_pro.md', pro_rebuttal)

            print(f'Round {round_count} | con rebuttal ...')
            
            # GENERATE con_argument(@topic, @pro_history) INTO @con_rebuttal
            con_rebuttal = run_single_task(
                con_agent,
                con_argument_prompt.format(topic=topic, previous=pro_history),
                "A focused rebuttal opposing the motion"
            )
            
            # @con_history := @con_history || '\n---\n' || @con_rebuttal
            con_history = con_history + '\n---\n' + con_rebuttal
            write_file(f'{log_dir}/round_{round_count}_con.md', con_rebuttal)

            # @round := @round + 1
            round_count = round_count + 1
            print(f'Round {round_count} complete')

        print('All rounds done — judge deliberating ...')

        # GENERATE judge_debate(@topic, @pro_history, @con_history) INTO @verdict
        verdict = run_single_task(
            judge_agent,
            judge_debate_prompt.format(topic=topic, pro_history=pro_history, con_history=con_history),
            "A verdict declaring the winner (PRO or CON) with reasoning (2-3 paragraphs)"
        )

        print(f'Verdict ready | rounds={round_count}')
        write_file(f'{log_dir}/verdict.md', verdict)
        
        # RETURN @verdict WITH status = 'complete', rounds = @round
        return {
            'verdict': verdict,
            'status': 'complete', 
            'rounds': round_count
        }

    except Exception as e:
        # EXCEPTION WHEN MaxIterationsReached THEN
        if 'MaxIterationsReached' in str(e):
            verdict = run_single_task(
                judge_agent,
                judge_debate_prompt.format(topic=topic, pro_history=pro_history, con_history=con_history),
                "A verdict declaring the winner (PRO or CON) with reasoning (2-3 paragraphs)"
            )
            return {
                'verdict': verdict,
                'status': 'partial'
            }
        # EXCEPTION WHEN BudgetExceeded THEN    
        elif 'BudgetExceeded' in str(e):
            return {
                'verdict': pro_history,
                'status': 'budget_limit'
            }
        else:
            raise e

if __name__ == "__main__":
    # Usage example matching SPL INPUT defaults
    result = debate_arena(
        topic='AI should be open-sourced',
        max_rounds=3,
        log_dir='cookbook/11_debate_arena/logs-spl',
        model='gemma3'
    )
    
    print("\n" + "="*50)
    print("DEBATE VERDICT")
    print("="*50)
    print(result['verdict'])
    print(f"\nStatus: {result['status']}")
    print(f"Rounds completed: {result['rounds']}")
