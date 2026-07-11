function result = linear_programming(f, A, b, Aeq, beq, lb, ub, sense)
%LINEAR_PROGRAMMING Solve a reusable linear program with linprog.
if nargin < 8 || isempty(sense)
    sense = "min";
end
if strcmpi(sense, "max")
    [x, fval, exitflag, output] = linprog(-f, A, b, Aeq, beq, lb, ub);
    fval = -fval;
else
    [x, fval, exitflag, output] = linprog(f, A, b, Aeq, beq, lb, ub);
end
result.x = x;
result.fval = fval;
result.exitflag = exitflag;
result.output = output;
end
