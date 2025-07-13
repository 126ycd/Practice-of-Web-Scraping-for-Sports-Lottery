import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib

# 配置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False  # 显示负号

# 定义请求头
headers = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'authorization_code': '',  # 如果有的话，填入授权码
    'connection': 'keep-alive',
    'host': 'i.cmzj.net',
    'origin': 'https://www.cmzj.net',
    'referer': 'https://www.cmzj.net/',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0'
}

# 专家ID列表
expert_ids = [
    1773113, 2512808, 1968450, 1922806, 2238909, 2249170, 1844660, 2043821,
    1243082, 2228560, 2382898, 2602585, 1784814, 1848315, 2584339, 1840573,
    2069148, 2091581, 2534580, 2158974
]

# 存储所有专家数据的列表
expert_data_list = []

# 遍历专家ID列表，获取每个专家的数据
for expert_id in expert_ids:
    url = f"https://i.cmzj.net/expert/queryExpertById?expertId={expert_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        expert_data = response.json()  # 获取JSON格式的数据
        # 解析每个专家的基本信息和表现
        expert_info = {
            '专家ID': expert_data['data']['expertId'],
            '姓名': expert_data['data']['name'],
            '彩龄': expert_data['data']['age'],  # 彩龄
            '发文量': expert_data['data']['articles'],  # 发文量
            '大乐透中奖次数': expert_data['data']['dltOne'],  # 大乐透中奖次数
        }
        expert_data_list.append(expert_info)
    else:
        print(f"专家ID {expert_id} 请求失败，状态码: {response.status_code}")

# 将所有专家数据转化为 DataFrame 进行分析
expert_df = pd.DataFrame(expert_data_list)

# 打印友好的数据描述输出
print("\n统计数据描述：\n")
print(expert_df.describe())

# 生成更友好的文字输出
output = """
    专家基本统计信息：
    --------------------
    - 彩龄（平均值）：{0:.2f}年
    - 发文量（平均值）：{1:.2f}篇
    - 大乐透中奖次数（平均值）：{2:.2f}次
""".format(
    expert_df['彩龄'].mean(),
    expert_df['发文量'].mean(),
    expert_df['大乐透中奖次数'].mean(),
)

print(output)

# 保存数据到CSV文件
output_file = "专家数据分析.csv"
expert_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n数据已保存到 {output_file}")

# 保存数据到Excel文件
output_excel = "专家数据分析.xlsx"
expert_df.to_excel(output_excel, index=False)  # 不需要encoding参数
print(f"数据已保存到 {output_excel}")

# 可视化：分析发文量与大乐透中奖次数的关系
plt.figure(figsize=(10, 6))
sns.scatterplot(data=expert_df, x='发文量', y='大乐透中奖次数')
plt.title("发文量与大乐透中奖次数的关系")
plt.xlabel("发文量")
plt.ylabel("大乐透中奖次数")
plt.savefig('发文量与大乐透中奖次数.png')  # 保存为PNG图片
plt.show()

# 可视化：分析彩龄与大乐透中奖次数的关系
plt.figure(figsize=(10, 6))
sns.scatterplot(data=expert_df, x='彩龄', y='大乐透中奖次数')
plt.title("彩龄与大乐透中奖次数的关系")
plt.xlabel("彩龄")
plt.ylabel("大乐透中奖次数")
plt.savefig('彩龄与大乐透中奖次数.png')  # 保存为PNG图片
plt.show()
