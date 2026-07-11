function result = integer_programming(f, intcon, A, b, Aeq, beq, lb, ub)
%INTEGER_PROGRAMMING Solve an integer program with intlinprog.
[x, fval, exitflag, output] = intlinprog(f, intcon, A, b, Aeq, beq, lb, ub);
result.x = x;
result.fval = fval;
result.exitflag = exitflag;
result.output = output;
end
