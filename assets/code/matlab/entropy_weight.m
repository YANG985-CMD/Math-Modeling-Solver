function result = entropy_weight(data, benefitMask)
%ENTROPY_WEIGHT Compute entropy weights and weighted scores.
if nargin < 2 || isempty(benefitMask)
    benefitMask = true(1, size(data, 2));
end
normalized = zeros(size(data));
for j = 1:size(data, 2)
    column = data(:, j);
    cmin = min(column);
    cmax = max(column);
    if cmax == cmin
        continue;
    end
    if benefitMask(j)
        normalized(:, j) = (column - cmin) ./ (cmax - cmin);
    else
        normalized(:, j) = (cmax - column) ./ (cmax - cmin);
    end
end
proportions = normalized ./ max(sum(normalized, 1), eps);
k = 1 / log(size(data, 1));
entropy = -k * sum(proportions .* log(proportions + eps), 1);
divergence = 1 - entropy;
weights = divergence ./ sum(divergence);
scores = normalized * weights';
result.weights = weights;
result.scores = scores;
result.normalized = normalized;
end
