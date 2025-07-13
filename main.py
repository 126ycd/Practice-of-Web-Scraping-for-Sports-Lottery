import os
import time
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import matplotlib.font_manager as fm

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 设置 ChromeDriver 路径
chrome_driver_path = r"C:\chromedriver-win64\chromedriver.exe"


def crawl_dlt_data():
    """爬取大乐透开奖数据"""
    if not os.path.exists(chrome_driver_path):
        raise FileNotFoundError(f"[错误] ChromeDriver 不存在，请下载并放置到路径: {chrome_driver_path}")

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(executable_path=chrome_driver_path)
    service.log_path = "chromedriver.log"

    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("[成功] 浏览器启动成功")

        url = "https://www.zhcw.com/kjxx/dlt/"
        driver.get(url)
        print(f"[访问] 正在加载 URL: {url}")

        # 增加等待时间和更多容错处理
        wait = WebDriverWait(driver, 30)

        # 等待页面加载完成
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "flcp")))
        print("[成功] 页面加载完成")

        # 点击"近100期"按钮
        print("[操作] 尝试点击'近100期'按钮...")
        try:
            # 定位"近100期"按钮
            period_100_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//span[contains(@class, "annq") and contains(text(), "近100期")]'))
            )
            # 滚动到元素位置确保可见
            driver.execute_script("arguments[0].scrollIntoView();", period_100_button)
            time.sleep(1)
            # 点击按钮
            period_100_button.click()
            print("[成功] 已点击'近100期'按钮")

            # 等待数据加载完成
            print("[等待] 等待100期数据加载...")
            time.sleep(3)

            # 使用更精确的等待条件：等待分页控件出现
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pagination")))
            print("[成功] 100期数据加载完成")

        except Exception as e:
            print(f"[警告] 无法点击'近100期'按钮: {e}")
            print("[尝试] 直接访问100期URL...")
            driver.get("https://www.zhcw.com/kjxx/dlt/?kjData=100")
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "flcp")))
            print("[成功] 已加载100期数据")

        # 获取总页数
        try:
            pagination = driver.find_element(By.CLASS_NAME, "pagination")
            page_links = pagination.find_elements(By.TAG_NAME, "a")
            last_page_link = page_links[-2]  # 倒数第二个是最后一页
            total_pages = int(last_page_link.text) if last_page_link.text.isdigit() else 1
            print(f"[信息] 总页数: {total_pages}")
        except Exception as e:
            print(f"[警告] 无法获取总页数: {e}, 默认使用1页")
            total_pages = 1

        # 提取所有页面数据
        all_data = []

        for page in range(1, total_pages + 1):
            print(f"[提取] 正在处理第 {page}/{total_pages} 页...")

            # 如果不是第一页，需要点击翻页
            if page > 1:
                try:
                    # 查找页码链接
                    page_link = wait.until(
                        EC.element_to_be_clickable((By.XPATH, f'//li/a[text()="{page}"]'))
                    )
                    # 滚动到元素位置
                    driver.execute_script("arguments[0].scrollIntoView();", page_link)
                    time.sleep(1)
                    # 点击页码
                    page_link.click()
                    print(f"[操作] 已跳转到第 {page} 页")

                    # 等待加载完成 - 等待当前页码变为激活状态
                    wait.until(
                        EC.presence_of_element_located((By.XPATH, f'//li[@class="active"]/a[text()="{page}"]'))
                    )
                    time.sleep(2)  # 额外等待确保数据加载
                except Exception as e:
                    print(f"[警告] 无法跳转到第 {page} 页: {e}")
                    continue

            # 提取当前页数据
            try:
                # 获取表格中的所有行
                rows = driver.find_elements(By.XPATH, '//div[@class="flcp"]//table//tbody//tr')
                print(f"  找到 {len(rows)} 行数据")

                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 14:  # 确保有足够的数据列
                        # 提取各列数据
                        period = cells[0].text.strip()
                        date_text = cells[1].text.strip()

                        # 清理日期文本（移除星期信息）
                        date_str = date_text.split("（")[0].strip()

                        # 提取前区号码
                        red_balls = [span.text for span in cells[2].find_elements(By.CLASS_NAME, "jqh")]
                        red_balls_str = ','.join(red_balls)

                        # 提取后区号码
                        blue_balls = [span.text for span in cells[3].find_elements(By.CLASS_NAME, "jql")]
                        blue_balls_str = ','.join(blue_balls)

                        sales = cells[4].text.strip().replace(",", "")
                        prize_pool = cells[13].text.strip().replace(",", "")  # 奖池奖金在第14列

                        all_data.append({
                            "期号": period,
                            "开奖日期": date_str,
                            "前区号码": red_balls_str,
                            "后区号码": blue_balls_str,
                            "总销售额(元)": float(sales) if sales else None,
                            "奖池奖金(元)": float(prize_pool) if prize_pool else None
                        })

            except Exception as e:
                print(f"[警告] 第 {page} 页数据提取失败: {e}")
                # 保存页面快照以便调试
                driver.save_screenshot(f"page_{page}_error.png")
                print(f"[已保存] 页面截图: page_{page}_error.png")

        if not all_data:
            print("[错误] 未提取到任何数据")
            return None

        print(f"[成功] 总共提取到 {len(all_data)} 期开奖数据")
        return pd.DataFrame(all_data)

    except Exception as e:
        print(f"[错误] 浏览器启动或操作失败: {e}")
        if 'driver' in locals():
            driver.save_screenshot("error_screenshot.png")
            print("[已保存] 错误截图: error_screenshot.png")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()
            print("[完成] 浏览器已关闭")


def analyze_sales_trend(df):
    """任务1：分析销售额趋势并预测下一期销售额"""
    print("\n===== 任务1：销售额趋势分析与预测 =====")

    # 转换日期格式
    df['开奖日期'] = pd.to_datetime(df['开奖日期'])
    df = df.sort_values('开奖日期')

    # 过滤截至2025年7月1日的数据
    cutoff_date = pd.Timestamp('2025-07-01')
    historical_df = df[df['开奖日期'] < cutoff_date]

    if len(historical_df) < 10:
        print("警告：历史数据不足，使用全部数据进行预测")
        historical_df = df

    # 销售额趋势分析
    plt.figure(figsize=(14, 7))
    plt.plot(historical_df['开奖日期'], historical_df['总销售额(元)'] / 1e6, 'o-', label='实际销售额')
    plt.title('大乐透总销售额趋势 (截至2025-07-01)', fontsize=15)
    plt.xlabel('开奖日期', fontsize=12)
    plt.ylabel('总销售额(百万元)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('sales_trend.png')
    print("[图表] 销售额趋势图已保存: sales_trend.png")

    # 销售额预测
    X = np.array(range(len(historical_df))).reshape(-1, 1)
    y = historical_df['总销售额(元)'].values

    # 训练线性回归模型
    model = LinearRegression()
    model.fit(X, y)

    # 预测下一期销售额
    next_date = historical_df['开奖日期'].max() + timedelta(days=2)  # 大乐透开奖间隔通常为2-3天
    next_index = len(historical_df)
    next_sale = model.predict([[next_index]])[0]

    # 绘制预测结果
    plt.figure(figsize=(14, 7))
    plt.plot(historical_df['开奖日期'], y / 1e6, 'o-', label='历史销售额')

    # 预测点
    plt.scatter([next_date], [next_sale / 1e6], color='red', s=100, label='预测销售额')

    # 预测趋势线
    future_dates = historical_df['开奖日期'].tolist() + [next_date]
    future_X = np.array(range(len(future_dates))).reshape(-1, 1)
    future_y = model.predict(future_X)

    plt.plot(future_dates, future_y / 1e6, 'r--', label='预测趋势')

    plt.title('大乐透总销售额趋势与预测', fontsize=15)
    plt.xlabel('开奖日期', fontsize=12)
    plt.ylabel('总销售额(百万元)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('sales_prediction.png')
    print("[图表] 销售额预测图已保存: sales_prediction.png")

    print(f"预测{next_date.strftime('%Y-%m-%d')}销售额: {next_sale:,.2f}元")
    return next_sale


def number_frequency_analysis(df):
    """任务2：号码频率统计与推荐"""
    print("\n===== 任务2：号码频率分析与推荐 =====")

    # 前区号码频率分析
    red_numbers = []
    for nums in df['前区号码']:
        red_numbers.extend([int(num) for num in nums.split(',')])

    # 后区号码频率分析
    blue_numbers = []
    for nums in df['后区号码']:
        blue_numbers.extend([int(num) for num in nums.split(',')])

    # 创建频率数据框
    red_freq = pd.Series(red_numbers).value_counts().sort_index()
    blue_freq = pd.Series(blue_numbers).value_counts().sort_index()

    # 转换为DataFrame便于分析
    red_df = pd.DataFrame({'前区号码': red_freq.index, '出现频率': red_freq.values})
    blue_df = pd.DataFrame({'后区号码': blue_freq.index, '出现频率': blue_freq.values})

    # 保存频率数据
    red_df.to_csv('red_number_frequency.csv', index=False, encoding='utf_8_sig')
    blue_df.to_csv('blue_number_frequency.csv', index=False, encoding='utf_8_sig')
    print("[数据] 前区号码频率已保存: red_number_frequency.csv")
    print("[数据] 后区号码频率已保存: blue_number_frequency.csv")

    # 可视化前区号码频率
    plt.figure(figsize=(14, 7))
    sns.barplot(x='前区号码', y='出现频率', data=red_df, hue='前区号码', palette='coolwarm', legend=False)
    plt.title('前区号码(1-35)出现频率', fontsize=15)
    plt.xlabel('前区号码', fontsize=12)
    plt.ylabel('出现次数', fontsize=12)
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('red_number_frequency.png')
    print("[图表] 前区号码频率图已保存: red_number_frequency.png")

    # 可视化后区号码频率
    plt.figure(figsize=(10, 6))
    sns.barplot(x='后区号码', y='出现频率', data=blue_df, hue='后区号码', palette='coolwarm', legend=False)
    plt.title('后区号码(1-12)出现频率', fontsize=15)
    plt.xlabel('后区号码', fontsize=12)
    plt.ylabel('出现次数', fontsize=12)
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('blue_number_frequency.png')
    print("[图表] 后区号码频率图已保存: blue_number_frequency.png")

    # 生成推荐号码
    # 策略：选择高频号码，但避免全部选择最高频的号码
    recommended_red = red_df.sort_values('出现频率', ascending=False).head(10).sample(5)['前区号码'].tolist()
    recommended_blue = blue_df.sort_values('出现频率', ascending=False).head(5).sample(2)['后区号码'].tolist()

    # 按数字大小排序
    recommended_red.sort()
    recommended_blue.sort()

    print(f"推荐投注号码：前区 {recommended_red} + 后区 {recommended_blue}")
    return recommended_red, recommended_blue


def day_of_week_analysis(df):
    """任务3：不同开奖日分析"""
    print("\n===== 任务3：开奖日对比分析 =====")

    # 转换日期并提取星期几
    df['开奖日期'] = pd.to_datetime(df['开奖日期'])
    df['星期'] = df['开奖日期'].dt.day_name()

    # 只保留周一、周三、周六
    valid_days = ['Monday', 'Wednesday', 'Saturday']
    df = df[df['星期'].isin(valid_days)]

    # 中文星期名称映射
    day_map = {
        'Monday': '周一',
        'Wednesday': '周三',
        'Saturday': '周六'
    }
    df['星期'] = df['星期'].map(day_map)

    # 按星期分组
    grouped = df.groupby('星期')

    # 销售额对比
    sales_by_day = grouped['总销售额(元)'].mean()

    # 保存销售额对比数据
    sales_df = pd.DataFrame({
        '开奖日': sales_by_day.index,
        '平均销售额(元)': sales_by_day.values
    })
    sales_df.to_csv('sales_by_day.csv', index=False, encoding='utf_8_sig')
    print("[数据] 开奖日销售额对比已保存: sales_by_day.csv")

    # 可视化销售额对比
    plt.figure(figsize=(10, 6))
    sales_by_day.plot(kind='bar', color=['skyblue', 'lightgreen', 'salmon'])
    plt.title('不同开奖日平均销售额对比', fontsize=15)
    plt.xlabel('开奖日', fontsize=12)
    plt.ylabel('平均销售额(元)', fontsize=12)
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('sales_by_day.png')
    print("[图表] 开奖日销售额对比图已保存: sales_by_day.png")

    # 号码分布分析
    # 前区号码分布
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for i, day in enumerate(['周一', '周三', '周六']):
        day_df = df[df['星期'] == day]

        # 提取前区号码
        red_numbers = []
        for nums in day_df['前区号码']:
            red_numbers.extend([int(num) for num in nums.split(',')])

        # 统计频率
        red_freq = pd.Series(red_numbers).value_counts().sort_index()
        red_df = pd.DataFrame({'前区号码': red_freq.index, '出现频率': red_freq.values})

        # 绘制分布图
        ax = axes[i]
        sns.barplot(x='前区号码', y='出现频率', data=red_df, hue='前区号码', palette='coolwarm', legend=False, ax=ax)
        ax.set_title(f'{day} - 前区号码分布', fontsize=14)
        ax.set_xlabel('前区号码', fontsize=12)
        ax.set_ylabel('出现次数', fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig('red_number_by_day.png')
    print("[图表] 开奖日前区号码分布图已保存: red_number_by_day.png")

    # 后区号码分布
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for i, day in enumerate(['周一', '周三', '周六']):
        day_df = df[df['星期'] == day]

        # 提取后区号码
        blue_numbers = []
        for nums in day_df['后区号码']:
            blue_numbers.extend([int(num) for num in nums.split(',')])

        # 统计频率
        blue_freq = pd.Series(blue_numbers).value_counts().sort_index()
        blue_df = pd.DataFrame({'后区号码': blue_freq.index, '出现频率': blue_freq.values})

        # 绘制分布图
        ax = axes[i]
        sns.barplot(x='后区号码', y='出现频率', data=blue_df, hue='后区号码', palette='coolwarm', legend=False, ax=ax)
        ax.set_title(f'{day} - 后区号码分布', fontsize=14)
        ax.set_xlabel('后区号码', fontsize=12)
        ax.set_ylabel('出现次数', fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig('blue_number_by_day.png')
    print("[图表] 开奖日后区号码分布图已保存: blue_number_by_day.png")

    return sales_by_day


def generate_report(df, next_sale, recommended_red, recommended_blue):
    """生成分析报告"""
    report = """
    ============================
        大乐透数据分析报告
    ============================

    一、数据概况
    -------------
    分析期数: {period_count}
    时间范围: {start_date} 至 {end_date}
    总销售额: {total_sales:.2f} 元
    平均每期销售额: {avg_sales:.2f} 元

    二、销售额趋势分析
    -------------
    基于历史数据预测下一期销售额:
    预测日期: {next_date}
    预测销售额: {next_sale:,.2f} 元

    三、号码频率分析
    -------------
    推荐投注号码:
    前区: {red_numbers}
    后区: {blue_numbers}

    四、报告说明
    -------------
    本报告基于中国体彩网公开数据分析生成
    生成时间: {report_time}
    """

    # 填充报告内容
    report = report.format(
        period_count=len(df),
        start_date=df['开奖日期'].min().strftime('%Y-%m-%d'),
        end_date=df['开奖日期'].max().strftime('%Y-%m-%d'),
        total_sales=df['总销售额(元)'].sum(),
        avg_sales=df['总销售额(元)'].mean(),
        next_date=(df['开奖日期'].max() + timedelta(days=2)).strftime('%Y-%m-%d'),
        next_sale=next_sale,
        red_numbers=", ".join(map(str, recommended_red)),
        blue_numbers=", ".join(map(str, recommended_blue)),
        report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # 保存报告
    with open('analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print("\n" + report)
    print("\n[报告] 分析报告已保存: analysis_report.txt")


if __name__ == "__main__":
    # 1. 爬取大乐透数据
    df = crawl_dlt_data()

    if df is not None:
        print("\n[数据预览]")
        print(df.head())
        print(f"总共获取 {len(df)} 期数据")

        # 保存原始数据
        csv_filename = "dlt_100_periods.csv"
        df.to_csv(csv_filename, index=False, encoding='utf_8_sig')
        print(f"原始数据已保存到: {csv_filename}")

        # 2. 任务1：销售额趋势分析与预测
        next_sale = analyze_sales_trend(df)

        # 3. 任务2：号码频率分析与推荐
        recommended_red, recommended_blue = number_frequency_analysis(df)

        # 4. 任务3：开奖日对比分析
        sales_by_day = day_of_week_analysis(df)

        # 5. 生成分析报告
        generate_report(df, next_sale, recommended_red, recommended_blue)

        print("\n所有任务已完成！所有图表和数据已保存到当前目录。")
    else:
        print("未能获取数据，请检查错误日志")