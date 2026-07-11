function result = particle_swarm(objectiveFcn, bounds, options)
%PARTICLE_SWARM Run a reusable particle swarm optimization wrapper.
if nargin < 3
    options = optimoptions("particleswarm", "Display", "off");
end
nvars = size(bounds, 1);
lb = bounds(:, 1)';
ub = bounds(:, 2)';
[x, fval, exitflag, output] = particleswarm(objectiveFcn, nvars, lb, ub, options);
result.x = x;
result.fval = fval;
result.exitflag = exitflag;
result.output = output;
end
