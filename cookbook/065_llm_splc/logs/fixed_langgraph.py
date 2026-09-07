FROM langgraph.components.base AS Base

WORKFLOW self_refine
  INPUT:
    @task TEXT := 'What are the benefits of meditation?',
    @output_budget INTEGER := 2000,
    @max_iterations INTEGER := 3,
    @writer_model TEXT := 'gemma3',
    @critic_model TEXT := 'llama3.2',
    @log_dir TEXT := 'cookbook/05_self_refine/logs-spl'
  OUTPUT: @result TEXT
DO
  @iteration := 0

  LOGGING f'Self-refine started | max_iterations={@max_iterations} for task:\n {@task} ...' LEVEL INFO

  -- Initial draft
  GENERATE draft(TEXT(@task)) WITH OUTPUT BUDGET @output_budget TOKENS
    USING MODEL @writer_model INTO @current
  LOGGING 'Initial draft ready' LEVEL INFO
  CALL write_file(f'{@log_dir}/draft_0.md', @current) INTO NONE

  -- Iterative refinement loop
  WHILE @iteration < @max_iterations DO
    LOGGING f'Iteration {@iteration} | critiquing ...' LEVEL DEBUG
    GENERATE critique(@current) WITH OUTPUT BUDGET @output_budget TOKENS
      USING MODEL @critic_model INTO @feedback
    CALL write_file(f'{@log_dir}/feedback_{@iteration}.md', @feedback) INTO NONE

    EVALUATE @feedback
      WHEN contains('[APPROVED]') THEN
        LOGGING f'Approved at iteration {@iteration}' LEVEL INFO
        GENERATE refine(@current, @feedback) WITH OUTPUT BUDGET @output_budget TOKENS
          USING MODEL @writer_model INTO @current
        CALL write_file(f'{@log_dir}/final.md', @current) INTO NONE
        RETURN @current WITH status = 'complete', iterations = @iteration
      ELSE
        @iteration := @iteration + 1
        GENERATE refine(@current, @feedback) WITH OUTPUT BUDGET @output_budget TOKENS
          USING MODEL @writer_model INTO @current
        LOGGING f'Refined | iteration={@iteration}' LEVEL DEBUG
        CALL write_file(f'{@log_dir}/draft_{@iteration}.md', @current) INTO NONE
    END
  END

  -- If loop exhausted, commit best effort
  LOGGING f'Max iterations reached | iterations={@iteration}' LEVEL WARN
  GENERATE draft(TEXT(@task)) WITH OUTPUT BUDGET @output_budget TOKENS
    USING MODEL @writer_model INTO @current
  CALL write_file(f'{@log_dir}/final.md', @current) INTO NONE
  RETURN @current WITH status = 'max_iterations', iterations = @iteration

EXCEPTION
  WHEN MaxIterationsReached THEN
    CALL write_file(f'{@log_dir}/final.md', @current) INTO NONE
    RETURN @current WITH status = 'partial'
  WHEN BudgetExceeded THEN
    RETURN @current WITH status = 'budget_limit'
END

WORKFLOW __main__
  INPUT: None
  OUTPUT: @result TEXT
DO
  @result := self_refine(task='What are the benefits of meditation?', output_budget=2000, max_iterations=3, writer_model='gemma3', critic_model='llama3.2', log_dir='cookbook/05_self_refine/logs-spl')
  LOGGING f'__main__ completed | result={@result}' LEVEL INFO
END
