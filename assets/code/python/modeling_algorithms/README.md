# Modeling Algorithms

这是一个可直接导入的轻量算法入口，适合先建立可执行基线：

```python
import sys
sys.path.insert(0, "assets/code/python")

from modeling_algorithms import entropy_weights, topsis, gm11

weights = entropy_weights(matrix, benefit_mask=[True, False])["weights"]
ranking = topsis(matrix, weights, benefit_mask=[True, False])["ranking"]
forecast = gm11([12, 13, 15, 18], forecast_steps=2)["forecast"]
```

返回值包含中间诊断，方便写入结果登记表。使用真实题目时仍必须补充题目适配、基线比较和独立验证；模板或高分指标不能代替证据。
