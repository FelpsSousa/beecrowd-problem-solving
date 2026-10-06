use std::io::{self, BufWriter, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin()
        .read_to_string(&mut input)
        .expect("failed to read stdin");
    let mut tokens = input.split_ascii_whitespace();

    let stdout = io::stdout();
    let mut out = BufWriter::new(stdout.lock());

    let n: i64 = tokens
        .next()
        .expect("missing n")
        .parse()
        .expect("n is not an integer");

    writeln!(out, "{n}").expect("failed to write stdout");
}
