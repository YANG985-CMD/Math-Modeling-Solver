function result = genetic_algorithm(objectiveFcn, bounds, options)
%GENETIC_ALGORITHM Run a reusable genetic algorithm wrapper.
if nargin < 3
    options = optimoptions("ga", "Display", "off");
end
nvars = size(bounds, 1);
lb = bounds(:, 1)';
ub = bounds(:, 2)';
[x, fval, exitflag, output] = ga(objectiveFcn, nvars, [], [], [], [], lb, ub, [], options);
result.x = x;
result.fval = fval;
result.exitflag = exitflag;
result.output = output;
end
