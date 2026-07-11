function result = grey_prediction(series, forecastSteps)
%GREY_PREDICTION Fit a GM(1,1) grey prediction model.
if nargin < 2
    forecastSteps = 1;
end
x0 = series(:);
x1 = cumsum(x0);
B = [-0.5 * (x1(1:end-1) + x1(2:end)), ones(numel(x0) - 1, 1)];
Y = x0(2:end);
params = B \ Y;
a = params(1);
b = params(2);
cumulative = @(k) (x0(1) - b / a) * exp(-a * k) + b / a;
fitted = zeros(size(x0));
fitted(1) = x0(1);
for idx = 2:numel(x0)
    fitted(idx) = cumulative(idx - 1) - cumulative(idx - 2);
end
forecast = zeros(forecastSteps, 1);
for idx = 1:forecastSteps
    forecast(idx) = cumulative(numel(x0) + idx - 1) - cumulative(numel(x0) + idx - 2);
end
residuals = x0 - fitted;
result.a = a;
result.b = b;
result.fitted = fitted;
result.forecast = forecast;
result.residuals = residuals;
result.posteriorErrorRatio = std(residuals) / std(x0);
result.smallErrorProbability = mean(abs(residuals - mean(residuals)) < 0.6745 * std(x0));
end
