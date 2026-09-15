async function getTasks() {
   const response = await fetch("http://127.0.0.1:8000/tasks");
   const tasks = await response.json();

   console.log("状态码：", response.status);
   for (const task of tasks) {
    if (task.done === false) {
        console.log(task.title);
    }
}
}

getTasks();