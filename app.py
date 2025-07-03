import streamlit as st
import pandas as pd
import re
from textblob import TextBlob
from wordcloud import WordCloud
import emoji
import matplotlib.pyplot as plt

st.title("WhatsApp Chat Analyzer")
st.write("Upload your WhatsApp chat (.txt) and explore insights")

# Upload WhatsApp chat file
uploaded_file = st.file_uploader("Upload your exported WhatsApp chat (.txt)", type="txt")

if uploaded_file is not None:
    chat_data = uploaded_file.read().decode("utf-8").splitlines()
    
    # Lists for parsed data
    dates, times, senders, messages = [], [], [], []

    # Regex pattern for WhatsApp format
    pattern = re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2})\s?([apAP][mM]) - (.*?): (.*)")

    for line in chat_data:
        match = pattern.match(line)
        if match:
            dates.append(match.group(1))
            times.append(f"{match.group(2)} {match.group(3).lower()}")
            senders.append(match.group(4))
            messages.append(match.group(5))

    # Build DataFrame
    df = pd.DataFrame({
        "Date": dates,
        "Time": times,
        "Sender": senders,
        "Message": messages
    })

    # Add combined Datetime column
    df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%y %I:%M %p", errors="coerce")

    # Sidebar menu
    st.sidebar.title("📂 Select a Feature to Analyze")
    feature = st.sidebar.selectbox("Choose Feature", [
        "Total Messages & Words Per User",
        "Total Messages per User",
        "Total Words per User",
        "Average Reply Time per User",
        "Who Starts Conversations the Most",
        "Who Ends Conversations the Most",
        "Average Message Length per User",
        "Top Words Per User (Word Cloud)",
        "Who tries to keep chats alive?",
        "Who replies faster?",
        "Whose messages are more positive?"
    ])

    if feature == "Total Messages & Words Per User":
        msg_counts = df["Sender"].value_counts()
        st.subheader("📨 Total messages per user:")
        st.write(msg_counts)

        df["Word Count"] = df["Message"].apply(lambda x: len(x.split()))
        word_counts = df.groupby("Sender")["Word Count"].sum().sort_values(ascending=False)
        st.subheader("✍️ Total words per user:")
        st.write(word_counts)

    elif feature == "Total Messages per User":
        st.header("Total Messages per User")
        msg_counts = df["Sender"].value_counts()
        st.subheader("📨 Total messages per user:")
        st.write(msg_counts)

    elif feature == "Total Words per User":
        st.header("Total Words per User")
        df["Word Count"] = df["Message"].apply(lambda x: len(x.split()))
        word_counts = df.groupby("Sender")["Word Count"].sum().sort_values(ascending=False)
        st.subheader("✍️ Total words per user:")
        st.write(word_counts)

    elif feature == "Average Reply Time per User":
        st.header("Average Reply Time per User")
        df["Previous Sender"] = df["Sender"].shift(1)
        df["Reply Time"] = df["Datetime"].diff().dt.total_seconds()
        reply_times = df[df["Sender"] != df["Previous Sender"]]
        reply_times_filtered = reply_times[reply_times["Reply Time"] <= (2 * 60 * 60)]
        avg_reply_times = reply_times_filtered.groupby("Sender")["Reply Time"].mean().sort_values()
        avg_reply_times_minutes = (avg_reply_times / 60).round(2)
        st.subheader("⏳ Average Reply Time (in minutes):")
        st.write(avg_reply_times_minutes)

    elif feature == "Who Starts Conversations the Most":
        st.header("Who Starts Conversations the Most")
        df["Time Gap"] = df["Datetime"].diff().dt.total_seconds()
        df["New Conversation"] = df["Time Gap"] > (30 * 60)
        conversation_starters = df[df["New Conversation"]]["Sender"].value_counts()
        st.subheader("💬 Conversation Starters:")
        st.write(conversation_starters)

    elif feature == "Who Ends Conversations the Most":
        st.header("Who Ends Conversations the Most")
        conversation_enders = df[df["New Conversation"].shift(-1, fill_value=False)]["Sender"].value_counts()
        st.subheader("🔚 Conversation Enders:")
        st.write(conversation_enders)

    elif feature == "Average Message Length per User":
        st.header("Average Message Length per User")
        df["Word Count"] = df["Message"].apply(lambda x: len(x.split()))
        avg_msg_length = df.groupby("Sender")["Word Count"].mean().sort_values(ascending=False)
        st.subheader("✍️ Average Message Length (words):")
        st.write(avg_msg_length)

    elif feature == "Top Words Per User (Word Cloud)":
        st.header("Top Words Per User (Word Cloud)")
        for sender in df["Sender"].unique():
            text = " ".join(df[df["Sender"] == sender]["Message"])
            wc = WordCloud(width=500, height=300, background_color="white").generate(text)
            st.subheader(f"☁️ Word Cloud for {sender}")
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

    elif feature == "Who tries to keep chats alive?":
        st.header("Who tries to keep chats alive?")
        df["Is_Question"] = df["Message"].apply(lambda x: x.strip().endswith("?"))
        extenders = df[df["Is_Question"]]["Sender"].value_counts()
        extenders_percent = (extenders / df["Sender"].value_counts()) * 100
        st.subheader("💬 Conversation Extender Score (% questions):")
        st.write(extenders_percent.round(2))

    elif feature == "Who replies faster?":
        st.header("Who replies faster?")
        df["Previous Sender"] = df["Sender"].shift(1)
        df["Reply Time"] = df["Datetime"].diff().dt.total_seconds()
        reply_times = df[df["Sender"] != df["Previous Sender"]]
        reply_times_filtered = reply_times[reply_times["Reply Time"] <= (2 * 60 * 60)]
        avg_reply_times = reply_times_filtered.groupby("Sender")["Reply Time"].mean().sort_values()
        avg_reply_times_minutes = (avg_reply_times / 60).round(2)
        st.subheader("⏳ Average Reply Time (in minutes):")
        st.write(avg_reply_times_minutes)

    elif feature == "Whose messages are more positive?":
        st.header("Whose messages are more positive?")
        df["Sentiment"] = df["Message"].apply(lambda x: TextBlob(x).sentiment.polarity)
        positive_ratio = df[df["Sentiment"] > 0].groupby("Sender").size() / df.groupby("Sender").size() * 100
        st.subheader("😊 Emotional Positivity Score (% positive messages):")
        st.write(positive_ratio.round(2))
