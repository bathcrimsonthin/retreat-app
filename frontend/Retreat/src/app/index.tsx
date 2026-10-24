import { Text, View, StyleSheet, Button } from "react-native";

export default function Index() {
  return (
    <View style={styles.container}>
      <Text>Press the button to post data.</Text>
      <Button title="Post Data" onPress={postData} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
});

const API_BASE_URL = "http://192.168.11.7:8000";

async function postData() {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, 
  {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      title: "Hello",
      minutes: 30,
    }),
  }
  )

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  const result = await response.json();
  console.log(result);
}
